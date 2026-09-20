import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/services/audio_service.dart';
import '../../../core/services/dummy_audio_service.dart';
import '../../../core/services/speech_service.dart';
import '../../../shared/models/chat_models.dart';
import '../../chat/presentation/chat_provider.dart';

// ── State enum ──────────────────────────────────────────────────────────────

enum VoiceConversationState {
  idle,
  initializing,
  listening,
  processing,
  responding,
  speaking,
  error,
  ended,
}

// ── State value object ───────────────────────────────────────────────────────

class VoiceState {
  final VoiceConversationState status;
  final String partialTranscript;
  final String? errorMessage;
  final String selectedLanguage; // "ne-NP" or "en-US"

  const VoiceState({
    required this.status,
    this.partialTranscript = '',
    this.errorMessage,
    this.selectedLanguage = 'ne-NP',
  });

  VoiceState copyWith({
    VoiceConversationState? status,
    String? partialTranscript,
    String? errorMessage,
    String? selectedLanguage,
  }) {
    return VoiceState(
      status: status ?? this.status,
      partialTranscript: partialTranscript ?? this.partialTranscript,
      // allow clearing the error with an explicit null
      errorMessage: errorMessage,
      selectedLanguage: selectedLanguage ?? this.selectedLanguage,
    );
  }

  bool get isActive =>
      status != VoiceConversationState.idle &&
      status != VoiceConversationState.ended &&
      status != VoiceConversationState.error;
}

// ── Providers ────────────────────────────────────────────────────────────────

final speechServiceProvider = Provider<SpeechService>((_) => SpeechToTextService());
final audioServiceProvider = Provider<AudioService>((_) => DummyAudioService());

final voiceProvider = NotifierProvider<VoiceNotifier, VoiceState>(VoiceNotifier.new);

// ── Notifier ─────────────────────────────────────────────────────────────────

/// Coordinates the full voice conversation loop:
///
///   listening → processing → responding → speaking → listening …
///
/// Important contracts:
///  1. Microphone is ALWAYS off while audio is playing (feedback prevention).
///  2. Only the FINAL transcript is forwarded to ChatNotifier.sendMessage().
///  3. VoiceNotifier never calls Dio directly — all backend work goes through
///     ChatNotifier so voice and typed chat share the exact same pipeline.
///  4. Playback failures never break the chat — text stays visible and the
///     conversation loop continues.
///  5. AI response audio is never generated on-device: the backend returns the
///     URL of a stored dummy recording which we simply play back.
class VoiceNotifier extends Notifier<VoiceState> {
  late final SpeechService _speech;
  late final AudioService _audio;

  StreamSubscription<String>? _partialSub;
  StreamSubscription<String>? _finalSub;
  StreamSubscription<void>? _audioCompleteSub;
  StreamSubscription<String>? _audioErrorSub;

  // Guard: prevents submitting the same final transcript twice.
  String? _lastSubmittedTranscript;

  // Guard: prevents overlapping sessions.
  bool _sessionActive = false;

  @override
  VoiceState build() {
    _speech = ref.read(speechServiceProvider);
    _audio = ref.read(audioServiceProvider);

    // Clean up when the provider is disposed (e.g. user leaves the screen).
    ref.onDispose(_cleanup);

    return const VoiceState(status: VoiceConversationState.idle);
  }

  // ── Public API ────────────────────────────────────────────────────────────

  /// Start a new voice conversation session.
  Future<void> startSession() async {
    if (_sessionActive) return; // Don't allow overlapping sessions.
    _sessionActive = true;
    _lastSubmittedTranscript = null;

    state = state.copyWith(
      status: VoiceConversationState.initializing,
      partialTranscript: '',
      errorMessage: null,
    );

    try {
      final available = await _speech.initialize();

      if (!available) {
        _setError('माइक्रोफोन प्रयोग गर्न अनुमति प्राप्त गरिएन। कृपया एप सेटिंग्स मा जाइर microphone अनुज्ञति दिनुहोस्।');
        return;
      }

      _subscribeSpeechStreams();
      _subscribeAudioStreams();
      await _startListening();
    } catch (e) {
      _setError('आवाज पहिचान सुरु गर्न सकिएन: $e');
    }
  }

  /// End the session from any state (user tapped stop).
  Future<void> endSession() async {
    await _stopMic();
    await _audio.stop();
    state = state.copyWith(
      status: VoiceConversationState.ended,
      partialTranscript: '',
    );
    _sessionActive = false;
    _cancelSubscriptions();
  }

  /// Interrupt audio playback and immediately start listening again.
  Future<void> interrupt() async {
    if (!_sessionActive) return;
    await _audio.stop();
    state = state.copyWith(
      status: VoiceConversationState.listening,
      partialTranscript: '',
    );
    await _startListening();
  }

  /// Change the recognition language. Audio playback is language-agnostic in
  /// the MVP (the same dummy recording is used regardless of language).
  Future<void> setLanguage(String locale) async {
    state = state.copyWith(selectedLanguage: locale);
  }

  // ── Internal flow ─────────────────────────────────────────────────────────

  Future<void> _startListening() async {
    if (!_sessionActive) return;
    state = state.copyWith(
      status: VoiceConversationState.listening,
      partialTranscript: '',
      errorMessage: null,
    );
    await _speech.startListening(state.selectedLanguage);
  }

  Future<void> _stopMic() async {
    await _speech.stopListening();
  }

  void _subscribeSpeechStreams() {
    _partialSub = _speech.partialResults.listen((partial) {
      if (!_sessionActive) return;

      // Detect error sentinel emitted by SpeechToTextService._onError.
      if (partial.startsWith('__ERROR__:')) {
        final msg = partial.replaceFirst('__ERROR__:', '');
        _handleSpeechError(msg);
        return;
      }

      if (state.status == VoiceConversationState.listening) {
        state = state.copyWith(partialTranscript: partial);
      }
    });

    _finalSub = _speech.finalResults.listen((final_) {
      if (!_sessionActive) return;
      _onFinalTranscript(final_);
    });
  }

  void _subscribeAudioStreams() {
    _audioCompleteSub = _audio.onPlaybackComplete.listen((_) {
      if (!_sessionActive) return;
      _onPlaybackComplete();
    });

    _audioErrorSub = _audio.onPlaybackError.listen((message) {
      if (!_sessionActive) return;
      debugPrint('[Voice] Audio playback error: $message');
      // Non-blocking: keep the state as-is but surface the message briefly.
      state = state.copyWith(errorMessage: message);
    });
  }

  void _onFinalTranscript(String transcript) {
    final trimmed = transcript.trim();
    if (trimmed.isEmpty) {
      // Empty transcript — resume listening.
      _startListening();
      return;
    }

    // Duplicate guard: same sentence must not be submitted twice.
    if (trimmed == _lastSubmittedTranscript) {
      debugPrint('[Voice] Duplicate transcript suppressed: $trimmed');
      _startListening();
      return;
    }
    _lastSubmittedTranscript = trimmed;

    // Transition to processing.
    state = state.copyWith(
      status: VoiceConversationState.processing,
      partialTranscript: '',
    );

    _forwardToChat(trimmed);
  }

  /// Send transcript to ChatNotifier (the ONLY place that calls the backend).
  Future<void> _forwardToChat(String text) async {
    final chatNotifier = ref.read(chatProvider.notifier);

    state = state.copyWith(status: VoiceConversationState.responding);

    try {
      // sendMessage() has its own isLoading guard — safe to call here.
      await chatNotifier.sendMessage(text);
    } catch (e) {
      // Network/parse error — surface in voice state.
      _setError(e.toString().replaceAll('Exception: ', ''));
      return;
    }

    // After sendMessage resolves, grab the latest AI message.
    final messages = ref.read(chatProvider).messages;
    final lastAi = messages.lastWhere(
      (m) => !m.isUser,
      orElse: () => ChatMessage(
        id: '',
        content: '',
        isUser: false,
        timestamp: DateTime.now(),
      ),
    );

    if (!_sessionActive) return;

    final audioUrl = lastAi.audioUrl;

    // No audio reference from the backend — keep the text visible, briefly
    // inform the user, then resume listening.
    if (audioUrl == null || audioUrl.trim().isEmpty) {
      debugPrint('[Voice] No audio_url in AI response; dummy audio unavailable.');
      state = state.copyWith(
        status: VoiceConversationState.speaking,
        errorMessage: 'आडियो उपलब्ध छैन।',
      );
      Future.delayed(const Duration(milliseconds: 800), () {
        if (_sessionActive) _onPlaybackComplete();
      });
      return;
    }

    // CRITICAL: microphone is already off (we're in processing/responding/
    // speaking). Play the stored dummy recording; the mic restarts only after
    // playback completes (see _onPlaybackComplete).
    state = state.copyWith(status: VoiceConversationState.speaking);

    try {
      await _audio.play(audioUrl);
      // _onPlaybackComplete() fires via _audioCompleteSub when playback ends.
    } catch (e) {
      // Defensive: a play-layer failure must never crash the loop. The text
      // answer is already in the chat; surface briefly and resume listening.
      debugPrint('[Voice] Audio playback crashed: $e');
      state = state.copyWith(
        status: VoiceConversationState.speaking,
        errorMessage: 'आडियो खेल्न सकिएन।',
      );
      Future.delayed(const Duration(milliseconds: 800), () {
        if (_sessionActive) _onPlaybackComplete();
      });
    }
  }

  /// Called when audio playback ends naturally.
  void _onPlaybackComplete() {
    if (!_sessionActive) return;
    if (state.status == VoiceConversationState.ended) return;

    // Auto-resume listening after the dummy audio finishes.
    _startListening();
  }

  void _handleSpeechError(String msg) {
    debugPrint('[Voice] Speech error: $msg');

    // For "no speech" we just restart listening quietly.
    if (msg.toLowerCase().contains('no speech') ||
        msg.toLowerCase().contains('speech timeout') ||
        msg.toLowerCase().contains('no_speech')) {
      if (_sessionActive) _startListening();
      return;
    }

    // For permission denied — show error and end.
    if (msg.toLowerCase().contains('permission') ||
        msg.toLowerCase().contains('not authorized')) {
      _setError('माइक्रोफोन प्रयोग गर्न अनुमति आवश्यक छ।');
      return;
    }

    // For other transient errors — show briefly then resume.
    state = state.copyWith(
      status: VoiceConversationState.error,
      errorMessage: 'आवाज पहिचान गर्न सकिएन। फेरि बोल्नुहोस्।',
    );
    if (_sessionActive) {
      Future.delayed(const Duration(seconds: 2), () {
        if (_sessionActive) _startListening();
      });
    }
  }

  void _setError(String message) {
    state = state.copyWith(
      status: VoiceConversationState.error,
      errorMessage: message,
      partialTranscript: '',
    );
    _sessionActive = false;
    _cancelSubscriptions();
  }

  Future<void> _cleanup() async {
    _sessionActive = false;
    _cancelSubscriptions();
    await _stopMic();
    await _audio.stop();
  }

  void _cancelSubscriptions() {
    _partialSub?.cancel();
    _finalSub?.cancel();
    _audioCompleteSub?.cancel();
    _audioErrorSub?.cancel();
    _partialSub = null;
    _finalSub = null;
    _audioCompleteSub = null;
    _audioErrorSub = null;
  }
}
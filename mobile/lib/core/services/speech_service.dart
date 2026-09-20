import 'dart:async';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_recognition_error.dart';

/// Abstract speech-to-text service contract.
/// Concrete implementations live behind this interface so the UI and
/// VoiceNotifier never depend directly on the underlying package.
abstract class SpeechService {
  /// Whether the service is currently listening.
  bool get isListening;

  /// Whether speech recognition is available on this device/browser.
  bool get isAvailable;

  /// Stream of intermediate (partial) transcripts while the user speaks.
  Stream<String> get partialResults;

  /// Stream that emits exactly once when a final transcript is ready.
  /// The stream emits the final recognized string.
  Stream<String> get finalResults;

  /// Initialize the recognizer and request permissions.
  /// Returns true if recognition is available.
  Future<bool> initialize();

  /// Start listening with the given [localeId] (e.g. "ne-NP" or "en-US").
  Future<void> startListening(String localeId);

  /// Stop listening and finalize any pending transcript.
  Future<void> stopListening();

  /// Release resources.
  Future<void> dispose();
}

/// Concrete implementation backed by the `speech_to_text` package.
class SpeechToTextService implements SpeechService {
  final stt.SpeechToText _speech = stt.SpeechToText();

  bool _available = false;
  bool _listening = false;

  // Controllers so callers can listen as streams.
  final _partialController = StreamController<String>.broadcast();
  final _finalController = StreamController<String>.broadcast();

  @override
  bool get isListening => _listening;

  @override
  bool get isAvailable => _available;

  @override
  Stream<String> get partialResults => _partialController.stream;

  @override
  Stream<String> get finalResults => _finalController.stream;

  @override
  Future<bool> initialize() async {
    _available = await _speech.initialize(
      onStatus: _onStatus,
      onError: _onError,
    );
    return _available;
  }

  @override
  Future<void> startListening(String localeId) async {
    if (!_available || _listening) return;

    await _speech.listen(
      onResult: _onResult,
      listenOptions: stt.SpeechListenOptions(
        localeId: localeId,
        partialResults: true,
        pauseFor: const Duration(seconds: 3),
        listenFor: const Duration(seconds: 60),
      ),
    );
    _listening = true;
  }

  @override
  Future<void> stopListening() async {
    if (!_listening) return;
    await _speech.stop();
    _listening = false;
  }

  @override
  Future<void> dispose() async {
    await stopListening();
    await _partialController.close();
    await _finalController.close();
  }

  // ── internal callbacks ──────────────────────────────────────────────────

  void _onResult(SpeechRecognitionResult result) {
    final words = result.recognizedWords.trim();
    if (words.isEmpty) return;

    if (result.finalResult) {
      _listening = false;
      _finalController.add(words);
    } else {
      _partialController.add(words);
    }
  }

  void _onStatus(String status) {
    // "done" and "notListening" mean recognition ended (possibly by silence).
    // We do NOT emit a finalResult here because _onResult already did so for
    // genuine speech endings, and we avoid double-firing.
    if (status == 'done' || status == 'notListening') {
      _listening = false;
    }
  }

  void _onError(SpeechRecognitionError error) {
    _listening = false;
    // Surface the error message as a partial-result sentinel so callers
    // can detect failures without a separate error stream.
    // We use a special prefix that VoiceNotifier watches for.
    _partialController.add('__ERROR__:${error.errorMsg}');
  }
}

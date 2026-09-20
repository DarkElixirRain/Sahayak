import 'dart:async';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';

import '../config.dart';
import 'audio_service.dart';

/// MVP implementation of [AudioService] that plays a pre-recorded dummy audio
/// file instead of generating speech dynamically.
///
/// The backend references a single stored audio file via the `audio_url` field
/// of every AI response. This service downloads/streams that file with
/// `audioplayers` and plays it.
///
/// When real dynamic TTS is enabled later, replace this service with a real
/// `RealTTSService` that also implements [AudioService] — no other part of the
/// voice flow needs to change.
class DummyAudioService implements AudioService {
  final AudioPlayer _player = AudioPlayer();
  final _completeController = StreamController<void>.broadcast();
  final _errorController = StreamController<String>.broadcast();

  bool _playing = false;
  bool _manualStop = false;

  StreamSubscription<void>? _completeSub;
  StreamSubscription<PlayerState>? _stateSub;

  DummyAudioService() {
    _completeSub = _player.onPlayerComplete.listen((_) => _handleCompleted());
    _stateSub = _player.onPlayerStateChanged.listen((state) {
      _playing = state == PlayerState.playing;
    });
  }

  @override
  bool get isPlaying => _playing;

  @override
  Stream<void> get onPlaybackComplete => _completeController.stream;

  @override
  Stream<String> get onPlaybackError => _errorController.stream;

  @override
  Future<void> play(String audioUrl) async {
    if (audioUrl.trim().isEmpty) {
      debugPrint('[DummyAudio] Empty audio URL provided.');
      _errorController.add('आडियो उपलब्ध छैन।');
      _completeController.add(null);
      return;
    }

    _manualStop = false;

    try {
      // Stop any previous playback first so two players never overlap.
      await _player.stop();
      _playing = true;

      if (audioUrl.startsWith('asset://')) {
        // Fully local demo audio — no network. Stored as a Flutter asset.
        final assetPath = audioUrl.replaceFirst('asset://', '');
        await _player.play(AssetSource(assetPath));
      } else {
        final uri = _resolveUrl(audioUrl);
        debugPrint('[DummyAudio] Playing: $uri');
        await _player.play(UrlSource(uri.toString()));
      }
    } catch (e) {
      debugPrint('[DummyAudio] play() failed: $e');
      _playing = false;
      _errorController.add('आडियो खेल्न सकिएन।');
      // Emit completion so the conversation loop advances (text stays visible).
      _completeController.add(null);
    }
  }

  @override
  Future<void> stop() async {
    _manualStop = true;
    _playing = false;
    try {
      await _player.stop();
    } catch (e) {
      debugPrint('[DummyAudio] stop() threw: $e');
    }
  }

  @override
  Future<void> dispose() async {
    await stop();
    await _completeSub?.cancel();
    await _stateSub?.cancel();
    await _player.dispose();
    await _completeController.close();
    await _errorController.close();
  }

  // ── helpers ──────────────────────────────────────────────────────────────

  void _handleCompleted() {
    _playing = false;
    if (_manualStop) {
      // Interrupted by the user (new interaction / stop) — not a natural end.
      _manualStop = false;
      return;
    }
    _completeController.add(null);
  }

  /// Turn a backend relative path (e.g. `/audio/dummy-response`) into an
  /// absolute URL using the app's configured API base URL.
  Uri _resolveUrl(String audioUrl) {
    if (audioUrl.startsWith('http://') || audioUrl.startsWith('https://')) {
      return Uri.parse(audioUrl);
    }
    final base = Uri.parse(AppConfig.baseUrl);
    final path = audioUrl.startsWith('/') ? audioUrl.substring(1) : audioUrl;
    return base.replace(path: '${base.path.replaceAll(RegExp(r'/*$'), '')}/$path');
  }
}
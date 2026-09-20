/// Abstract audio playback contract used by the voice conversation flow.
///
/// The voice pipeline depends only on this interface so that the concrete
/// backend can be swapped without touching the rest of the app:
///
///   VoiceNotifier → AudioService → DummyAudioService     (MVP today)
///   VoiceNotifier → AudioService → RealTTSService        (later)
abstract class AudioService {
  /// Whether audio playback is currently active.
  bool get isPlaying;

  /// Fires when playback ends naturally (audio finished playing).
  /// Interruptions via [stop] do NOT fire this stream.
  Stream<void> get onPlaybackComplete;

  /// Fires with a user-friendly message when audio fails to load or play.
  /// These failures are non-fatal: the caller keeps the text response visible.
  Stream<String> get onPlaybackError;

  /// Start playing the audio at [audioUrl].
  ///
  /// [audioUrl] may be an absolute URL or a path relative to the configured
  /// API base URL (e.g. "/audio/dummy-response").
  Future<void> play(String audioUrl);

  /// Stop any ongoing playback immediately. Does not emit [onPlaybackComplete].
  Future<void> stop();

  /// Release all resources.
  Future<void> dispose();
}
/// Central place for backend limits so the UI never hard-codes them twice.
///
/// Backend MVP (frozen):
///   - messages: max 2000 characters (MAX_MESSAGE_LENGTH in the route)
///   - audio: max 5 MB, max 30 seconds
abstract final class AppLimits {
  /// Backend rejects longer messages with 400.
  static const int maxMessageLength = 2000;

  /// Backend rejects larger audio files with 400.
  static const int maxAudioSizeMb = 5;

  /// Backend rejects longer recordings with 400.
  static const int maxAudioDurationSec = 30;
}

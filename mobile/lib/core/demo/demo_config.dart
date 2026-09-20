/// Central demo-mode configuration.
///
/// The whole app branches on [DemoConfig.demoMode]. When enabled, every
/// feature is served by the local demo data/assistant layer and NO network
/// requests are made. When disabled, the existing real backend services are
/// used unchanged.
///
/// Override at build time with:
///     flutter run --dart-define=DEMO_MODE=false
class DemoConfig {
  /// Master switch. Defaults to ON for the hackathon demo build.
  static const bool demoMode = bool.fromEnvironment('DEMO_MODE', defaultValue: true);

  /// Deterministic demo login credentials accepted by the local auth path.
  static const String demoUsername = 'bishal';
  static const String demoPassword = 'demo1234';

  /// Marker used as `audio_url` on demo responses. The audio service turns
  /// `asset://` URIs into local Flutter asset playback (fully offline).
  static const String demoAudioAsset = 'asset://audio/assistant_response.mp3';

  /// Dedicated offline voiceovers for the most common demo scenarios. Every
  /// scenario without a dedicated recording falls back to [demoAudioAsset].
  static const String audioBankOtp = 'asset://audio/bank_otp.mp3';
  static const String audioOtpShared = 'asset://audio/otp_shared.mp3';
  static const String audioDivorce = 'asset://audio/divorce.mp3';
  static const String audioLand = 'asset://audio/jagga.mp3';

  /// Simulated processing delay for demo responses so the UI feels alive
  /// without waiting on any backend.
  static const Duration responseDelay = Duration(milliseconds: 600);

  /// Delay used when playing back audio before resuming the mic.
  static const Duration audioFallbackResumeDelay = Duration(milliseconds: 500);
}
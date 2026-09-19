import 'package:flutter/foundation.dart';

class AppConfig {
  static const String appName = 'Sahayak';

  // Base API URL based on platform.
  // Use 10.0.2.2 for Android Emulator, 127.0.0.1 for iOS Simulator / Web.
  // This can be overridden with dart-defines in a real production build.
  static String get baseUrl {
    const String envBaseUrl = String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: '',
    );

    if (envBaseUrl.isNotEmpty) {
      return envBaseUrl;
    }

    if (kIsWeb) {
      return 'http://127.0.0.1:8000';
    } else if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    } else {
      return 'http://127.0.0.1:8000';
    }
  }
}

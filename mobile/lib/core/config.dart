import 'package:flutter/foundation.dart';

/// Configuration for the Sahayak app.
class AppConfig {
  /// Set this to your computer's LAN IP when testing on a physical device.
  /// Leave empty to use localhost (for emulator/simulator).
  static String lanIp = '10.10.60.158';

  /// The base URL for the API.
  static String get baseUrl {
    if (kReleaseMode) {
      // In production, use the production URL.
      // Set this to your production domain (e.g., 'https://api.example.com').
      return 'https://your-production-domain.com';
    } else {
      // In debug mode, use LAN IP if set, otherwise use localhost.
      if (lanIp.isNotEmpty) {
        return 'http://$lanIp:8000';
      } else {
        // Use localhost with emulator adjustment.
        // For Android emulator, use 10.0.2.2; for iOS simulator, use localhost.
        if (defaultTargetPlatform == TargetPlatform.android) {
          // Android emulator
          return 'http://10.0.2.2:8000';
        } else {
          // iOS simulator or other platforms (including web)
          return 'http://localhost:8000';
        }
      }
    }
  }
}
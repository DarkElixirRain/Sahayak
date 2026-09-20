import 'package:flutter/material.dart';

class AppColors {
  static const Color bgPage = Color(0xFFEEF0F5);
  static const Color purple1 = Color(0xFF7C6CF0);
  static const Color purple2 = Color(0xFF8B7BF5);
  static const Color pink1 = Color(0xFFF0A5C8);
  static const Color pink2 = Color(0xFFF6C9A8);
  static const Color orange1 = Color(0xFFF0784A);
  static const Color orange2 = Color(0xFFF5A35A);
  static const Color ink = Color(0xFF1E1B2E);
  static const Color inkSoft = Color(0xFF4A4560);
  static const Color muted = Color(0xFF8B87A0);
  
  static const Color cardBg = Color(0xB0FFFFFF); // #ffffffb0
  static const Color cardBorder = Color(0x80FFFFFF); // #ffffff80
  
  // Custom Gradients
  static const LinearGradient accentGradient = LinearGradient(
    colors: [purple1, pink1],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );

  static const LinearGradient purpleGradient = LinearGradient(
    colors: [purple1, purple2],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}

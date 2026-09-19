import 'package:flutter/material.dart';

/// Sahayak design system — extracted 1:1 from `ui/style.css`.
///
/// CSS custom properties:
///   --bg-page:#eef0f5; --purple-1:#7c6cf0; --purple-2:#8b7bf5;
///   --pink-1:#f0a5c8; --pink-2:#f6c9a8; --orange-1:#f0784a;
///   --orange-2:#f5a35a; --ink:#1e1b2e; --ink-soft:#4a4560;
///   --muted:#8b87a0; --card-bg:#ffffffb0; --card-border:#ffffff80;
abstract final class SahayakColors {
  // Core palette (from :root in style.css)
  static const bgPage = Color(0xFFeef0f5);
  static const purple1 = Color(0xFF7c6cf0);
  static const purple2 = Color(0xFF8b7bf5);
  static const purpleDeep = Color(0xFF6a58e0); // card-icon.purple end, filled btn end
  static const pink1 = Color(0xFFf0a5c8);
  static const pink2 = Color(0xFFf6c9a8);
  static const orange1 = Color(0xFFf0784a);
  static const orange2 = Color(0xFFf5a35a);
  static const ink = Color(0xFF1e1b2e);
  static const inkSoft = Color(0xFF4a4560);
  static const muted = Color(0xFF8b87a0);
  static const cardBg = Color(0xb0ffffff); // #ffffffb0
  static const cardBorder = Color(0x80ffffff); // #ffffff80

  // Accent gradient used on .s1-heading .accent and .s1-cta .label
  static const headingGradient = LinearGradient(
    colors: [purple1, Color(0xFFc56bd6)],
  );
  static const filledBtnGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [purple1, purpleDeep],
  );
  static const purpleIconGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF8f7ef2), purpleDeep],
  );
  static const orangeIconGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFf5875a), Color(0xFFe85f5f)],
  );
  static const pinkIconGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFf2879c), Color(0xFFe8617e)],
  );
  static const goBtnGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [purple1, purple2],
  );

  /// Voice screen mic: radial-gradient(circle at 35% 30%, #6d7cf5, #3a3fbf 70%)
  static const micGradient = RadialGradient(
    center: Alignment(-0.3, -0.4), // 35% 30%
    radius: 1.4,
    colors: [Color(0xFF6d7cf5), Color(0xFF3a3fbf)],
    stops: [0.0, 0.7],
  );

  /// Body background of the HTML page — layered radial washes over --bg-page.
  /// Used as the base for screen backgrounds (s1/s2 variants add more blooms).
  static List<BoxShadow> cardShadow(BuildContext context) => [
        BoxShadow(
          color: const Color(0xFF46366e).withValues(alpha: .12),
          blurRadius: 24,
          offset: const Offset(0, 10),
          spreadRadius: -14,
        ),
      ];

  static BoxDecoration glassCard(BuildContext context) => BoxDecoration(
        color: Theme.of(context).brightness == Brightness.dark
            ? Colors.white.withValues(alpha: .08)
            : cardBg,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.white.withValues(alpha: .5)),
        boxShadow: cardShadow(context),
      );
}

/// Screen background painters reproducing the layered radial gradients from
/// `.s1`, `.s2`, `.s3` in style.css.
class SahayakBackground extends StatelessWidget {
  final Widget child;
  final SahayakBgVariant variant;

  const SahayakBackground({
    super.key,
    required this.child,
    this.variant = SahayakBgVariant.home,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      decoration: BoxDecoration(
        gradient: switch (variant) {
          SahayakBgVariant.onboarding => _s1(isDark),
          SahayakBgVariant.home => _s2(isDark),
          SahayakBgVariant.voice => _s3(isDark),
        },
      ),
      child: child,
    );
  }

  static LinearGradient _base(bool isDark) => LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: isDark
            ? const [Color(0xFF171423), Color(0xFF15131f), Color(0xFF141625)]
            : const [Color(0xFFf2ece6), Color(0xFFece7f2), Color(0xFFe9ecf5)],
        stops: const [0.0, 0.55, 1.0],
      );

  /// .s1: blooms at 75%/15% purple, 10%/55% blue, 80%/85% orange
  static Gradient _s1(bool isDark) => LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        transform: const GradientRotation(0),
        colors: _base(isDark).colors,
      );

  /// .s2 background — blooms: purple top-right, blue left, orange bottom-right
  static Gradient _s2(bool isDark) => _base(isDark);

  /// .s3: simple vertical wash
  static Gradient _s3(bool isDark) => LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: isDark
            ? const [Color(0xFF181522), Color(0xFF16141f), Color(0xFF141725)]
            : const [Color(0xFFefeae4), Color(0xFFe7e3ef), Color(0xFFe3e7f2)],
        stops: const [0.0, 0.45, 1.0],
      );
}

enum SahayakBgVariant { onboarding, home, voice }

/// Builds the light/dark ThemeData used app-wide.
ThemeData buildSahayakTheme(Brightness brightness) {
  final isDark = brightness == Brightness.dark;
  const fontFamily = 'Noto Sans Devanagari';

  final scheme = ColorScheme(
    brightness: brightness,
    primary: SahayakColors.purple1,
    onPrimary: Colors.white,
    primaryContainer: isDark
        ? const Color(0xFF2b2650)
        : const Color(0xFFe6e2fc),
    onPrimaryContainer: isDark ? Colors.white : SahayakColors.purpleDeep,
    secondary: SahayakColors.orange1,
    onSecondary: Colors.white,
    secondaryContainer: isDark
        ? const Color(0xFF4a2a20)
        : const Color(0xFFffe8dd),
    onSecondaryContainer: isDark ? Colors.white : const Color(0xFF8a3c1c),
    error: const Color(0xFFba1a1a),
    onError: Colors.white,
    surface: isDark ? const Color(0xFF191622) : Colors.white,
    onSurface: isDark ? const Color(0xFFe6e1ec) : SahayakColors.ink,
    surfaceContainerHighest: isDark
        ? const Color(0xFF232030)
        : const Color(0xFFf2f0f7),
    onSurfaceVariant: isDark ? SahayakColors.muted : SahayakColors.inkSoft,
    outline: isDark
        ? Colors.white.withValues(alpha: .18)
        : Colors.black.withValues(alpha: .12),
    outlineVariant: isDark
        ? Colors.white.withValues(alpha: .10)
        : Colors.black.withValues(alpha: .08),
  );

  return ThemeData(
    useMaterial3: true,
    fontFamily: fontFamily,
    colorScheme: scheme,
    scaffoldBackgroundColor:
        isDark ? const Color(0xFF141221) : SahayakColors.bgPage,
    appBarTheme: AppBarTheme(
      centerTitle: false,
      elevation: 0,
      backgroundColor: Colors.transparent,
      foregroundColor: scheme.onSurface,
      titleTextStyle: TextStyle(
        fontFamily: fontFamily,
        fontSize: 19,
        fontWeight: FontWeight.w700,
        color: scheme.onSurface,
      ),
    ),
    textTheme: TextTheme(
      displayLarge: TextStyle(
        fontSize: 34,
        fontWeight: FontWeight.w700,
        height: 1.28,
        color: scheme.onSurface,
      ),
      headlineMedium: TextStyle(
        fontSize: 23,
        fontWeight: FontWeight.w700,
        color: scheme.onSurface,
      ),
      titleLarge: TextStyle(
        fontSize: 19,
        fontWeight: FontWeight.w700,
        color: scheme.onSurface,
      ),
      titleMedium: TextStyle(
        fontSize: 15,
        fontWeight: FontWeight.w700,
        color: scheme.onSurface,
      ),
      bodyLarge: TextStyle(
        fontSize: 15,
        fontWeight: FontWeight.w500,
        height: 1.4,
        color: scheme.onSurface,
      ),
      bodyMedium: TextStyle(
        fontSize: 14,
        height: 1.4,
        color: scheme.onSurface,
      ),
      bodySmall: TextStyle(
        fontSize: 12,
        height: 1.4,
        color: scheme.onSurfaceVariant,
      ),
      labelLarge: TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w700,
        color: scheme.onSurface,
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: isDark ? Colors.white.withValues(alpha: .06) : Colors.white.withValues(alpha: .75),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: Colors.white.withValues(alpha: .5)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(
          color: isDark
              ? Colors.white.withValues(alpha: .16)
              : Colors.white.withValues(alpha: .8),
        ),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: SahayakColors.purple1, width: 1.6),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: SahayakColors.purple1,
        foregroundColor: Colors.white,
        elevation: 0,
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 24),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        textStyle: const TextStyle(
          fontFamily: fontFamily,
          fontSize: 14,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: isDark ? const Color(0xFF3a2a3f) : SahayakColors.ink,
      contentTextStyle: TextStyle(
        fontFamily: fontFamily,
        color: Colors.white,
        fontSize: 13.5,
      ),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
  );
}

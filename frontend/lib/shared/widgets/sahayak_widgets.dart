import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../app/theme/sahayak_theme.dart';

/// Glass pill container used for `.s2-help`, `.session-item`, composer, etc.
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double borderRadius;
  final VoidCallback? onTap;

  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.borderRadius = 22,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: Ink(
        decoration: SahayakColors.glassCard(context).copyWith(
          borderRadius: BorderRadius.circular(borderRadius),
        ),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(borderRadius),
          child: Padding(padding: padding, child: child),
        ),
      ),
    );
  }
}

/// Gradient rounded square icon tile: `.card-icon.purple/.orange/.pink`.
class GradientIconTile extends StatelessWidget {
  final IconData icon;
  final Gradient gradient;
  final double size;

  const GradientIconTile({
    super.key,
    required this.icon,
    required this.gradient,
    this.size = 36,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        gradient: gradient,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Icon(icon, color: Colors.white, size: size * 0.47),
    );
  }
}

/// `.s1-cta` pill: gradient circle button + centered gradient label + chevron.
class GoPillButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const GoPillButton({super.key, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: Ink(
        decoration: BoxDecoration(
          color: Theme.of(context).brightness == Brightness.dark
              ? Colors.white.withValues(alpha: .10)
              : const Color(0xb3ffffff), // #ffffffb3
          borderRadius: BorderRadius.circular(40),
          border: Border.all(color: Colors.white.withValues(alpha: .6)),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF5a468c).withValues(alpha: .30),
              blurRadius: 30,
              offset: const Offset(0, 14),
              spreadRadius: -12,
            ),
          ],
        ),
        child: InkWell(
          borderRadius: BorderRadius.circular(40),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(8, 8, 10, 8),
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: const BoxDecoration(
                    gradient: SahayakColors.goBtnGradient,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: Color(0xb37c6cf0),
                        blurRadius: 16,
                        offset: Offset(0, 6),
                        spreadRadius: -4,
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.chevron_right,
                    color: Colors.white,
                    size: 22,
                  ),
                ),
                Expanded(
                  child: ShaderMask(
                    shaderCallback: (bounds) =>
                        SahayakColors.headingGradient.createShader(bounds),
                    child: Text(
                      label,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
                Icon(
                  Icons.keyboard_double_arrow_right,
                  size: 14,
                  color: SahayakColors.purple1.withValues(alpha: .7),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Small circular frosted button (`.s3-back`, `.s3-round`).
class FrostedCircleButton extends StatelessWidget {
  final Widget child;
  final VoidCallback? onTap;
  final double size;
  final String? semanticLabel;

  const FrostedCircleButton({
    super.key,
    required this.child,
    this.onTap,
    this.size = 48,
    this.semanticLabel,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: semanticLabel,
      child: Material(
        color: Colors.transparent,
        child: Ink(
          width: size,
          height: size,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Theme.of(context).brightness == Brightness.dark
                ? Colors.white.withValues(alpha: .10)
                : const Color(0xc0ffffff),
            border: Border.all(color: Colors.white.withValues(alpha: .7)),
          ),
          child: InkWell(
            customBorder: const CircleBorder(),
            onTap: onTap,
            child: Center(child: child),
          ),
        ),
      ),
    );
  }
}

/// Home screen avatar (`.s2-avatar`): soft blue circle with two glowing eyes.
class BotAvatar extends StatelessWidget {
  final double radius;

  const BotAvatar({super.key, this.radius = 21});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: radius * 2,
      height: radius * 2,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFdfeaf5), Color(0xFFb9cfe4)],
        ),
        border: Border.all(color: Colors.white.withValues(alpha: .63), width: 2),
      ),
      child: Center(          child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final _ in List.filled(2, 0))
              Container(
                width: 6,
                height: 6,
                margin: const EdgeInsets.symmetric(horizontal: 2),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: const Color(0xFFff9d3d),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFFff9d3d).withValues(alpha: .6),
                      blurRadius: 4,
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// CSS-shaped robot mascot from Screen 1 (`.bot` and children).
class SahayakBot extends StatelessWidget {
  final double width;
  const SahayakBot({super.key, this.width = 220});

  @override
  Widget build(BuildContext context) {
    final s = width / 220.0; // scale factor relative to the CSS 220x230 box

    Widget piece({
      required double left,
      required double top,
      required double w,
      required double h,
      required List<Color> colors,
      required double radius,
      double rotation = 0,
      List<BoxShadow> shadow = const [],
    }) {
      return Positioned(
        left: left * s,
        top: top * s,
        child: Transform.rotate(
          angle: rotation * math.pi / 180,
          child: Container(
            width: w * s,
            height: h * s,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: colors,
              ),
              borderRadius: BorderRadius.circular(radius * s),
              boxShadow: shadow,
            ),
          ),
        ),
      );
    }

    const light = [Color(0xFFe9f3fb), Color(0xFFb9d2e5)];
    const headColors = [Color(0xFFeaf6ff), Color(0xFFbcd8ee), Color(0xFF9fc3e0)];
    const bodyColors = [Color(0xFFf3f8fc), Color(0xFFcfe1ef), Color(0xFFb7cfe2)];
    const dark = [Color(0xFF2a3550), Color(0xFF182238)];

    return SizedBox(
      width: width,
      height: 230 * s,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          // Ears
          piece(
              left: 14, top: 34, w: 14, h: 34, colors: light, radius: 8),
          piece(
              left: 192, top: 34, w: 14, h: 34, colors: light, radius: 8),
          // Body
          piece(
            left: 46,
            top: 118,
            w: 128,
            h: 100,
            colors: bodyColors,
            radius: 34,
            shadow: [
              BoxShadow(
                color: const Color(0xFF3c5a82).withValues(alpha: .25),
                blurRadius: 20,
                offset: const Offset(0, 10),
                spreadRadius: -10,
              ),
            ],
          ),
          // Body panel dots
          Positioned(
            left: (46 + 60) * s,
            top: (118 + 14) * s,
            child: Column(
              children: [
                for (final _ in List.filled(3, 0))
                  Container(
                    width: 8 * s,
                    height: 8 * s,
                    margin: EdgeInsets.only(bottom: 16 * s),
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      color: Color(0xFF8fb7d6),
                    ),
                  ),
              ],
            ),
          ),
          // Arms
          piece(
              left: 14,
              top: 132,
              w: 26,
              h: 70,
              colors: light,
              radius: 14,
              rotation: 8),
          piece(
              left: 180,
              top: 132,
              w: 26,
              h: 70,
              colors: light,
              radius: 14,
              rotation: -8),
          // Hands
          piece(left: 10, top: 196, w: 22, h: 22, colors: dark, radius: 11),
          piece(left: 188, top: 196, w: 22, h: 22, colors: dark, radius: 11),
          // Legs
          piece(left: 58, top: 206, w: 30, h: 26, colors: light, radius: 12),
          piece(left: 132, top: 206, w: 30, h: 26, colors: light, radius: 12),
          // Feet
          piece(left: 56, top: 222, w: 34, h: 16, colors: dark, radius: 10),
          piece(left: 130, top: 222, w: 34, h: 16, colors: dark, radius: 10),
          // Head (on top of body)
          Positioned(
            left: 30 * s,
            top: 0,
            child: Container(
              width: 160 * s,
              height: 130 * s,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: headColors,
                  stops: const [0.0, 0.55, 1.0],
                ),
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(80 * s),
                  topRight: Radius.circular(80 * s),
                  bottomLeft: Radius.circular(64 * s),
                  bottomRight: Radius.circular(64 * s),
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF3c5a82).withValues(alpha: .30),
                    blurRadius: 24,
                    offset: const Offset(0, 12),
                    spreadRadius: -10,
                  ),
                ],
              ),
            ),
          ),
          // Face visor
          Positioned(
            left: 52 * s,
            top: 30 * s,
            child: Container(
              width: 116 * s,
              height: 56 * s,
              decoration: BoxDecoration(
                color: const Color(0xFF182238),
                borderRadius: BorderRadius.circular(30 * s),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  // Eyes with orange glow
                  for (final _ in List.filled(2, 0))
                    Container(
                      width: 26 * s,
                      height: 26 * s,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: const Color(0xFFff9d3d),
                          width: 3 * s,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFFffb356).withValues(alpha: .53),
                            blurRadius: 10,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ),
          // Mouth (teal bar inside visor, bottom-center)
          Positioned(
            left: 52 * s + 58 * s - 8 * s,
            top: 30 * s + 56 * s - 19 * s,
            child: Container(
              width: 16 * s,
              height: 5 * s,
              decoration: BoxDecoration(
                color: const Color(0xFF3ee6b0),
                borderRadius: BorderRadius.circular(3 * s),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Chat typing indicator — three pulsing dots (Screen 1 `.s1-dots` style).
class TypingDots extends StatefulWidget {
  const TypingDots({super.key});

  @override
  State<TypingDots> createState() => _TypingDotsState();
}

class _TypingDotsState extends State<TypingDots>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1200),
  )..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (var i = 0; i < 3; i++)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 3),
                child: Opacity(
                  opacity: 0.35 +
                      0.65 *
                          (0.5 +
                              0.5 *
                                  math.sin(
                                    (_controller.value * 2 * math.pi) +
                                        (i * math.pi / 3),
                                  )),
                  child: Container(
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: SahayakColors.purple1,
                    ),
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}

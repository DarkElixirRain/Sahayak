import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:go_router/go_router.dart';

import '../../../shared/widgets/sahayak_widgets.dart';
import '../../../app/theme/sahayak_theme.dart';

/// HTML Screen 1 — onboarding.
///
/// Reproduces `.s1`: layered pastel background, heading with gradient accent,
/// "म साथमा छु।" bubble with typing dots, the CSS robot mascot, and the
/// "सुरु गर्नुहोस्" CTA pill.
class WelcomeScreen extends HookWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Simple bubble entrance animation (fade+slide) matching the soft feel
    // of the mockup without heavy motion.
    final bubbleIn = useState(0.0);
    useEffect(() {
      Future.microtask(() => bubbleIn.value = 1);
      return null;
    }, []);

    return Scaffold(
      body: SahayakBackground(
        variant: SahayakBgVariant.onboarding,
        child: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(30, 28, 30, 0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 14),
                      // .s1-heading
                      Text.rich(
                        TextSpan(
                          children: [
                            const TextSpan(text: 'तपाईंको आफ्नै\nकानुनी साथी\n'),
                            TextSpan(
                              text: 'सहायक',
                              style: TextStyle(
                                // .accent: gradient text
                                foreground: Paint()
                                  ..shader = SahayakColors.headingGradient
                                      .createShader(
                                    const Rect.fromLTWH(0, 0, 200, 70),
                                  ),
                              ),
                            ),
                          ],
                        ),
                        style: const TextStyle(
                          fontSize: 34,
                          height: 1.28,
                          fontWeight: FontWeight.w700,
                          color: SahayakColors.ink,
                        ),
                      ),
                      const SizedBox(height: 26),
                      // .s1-bubble
                      AnimatedSlide(
                        duration: const Duration(milliseconds: 500),
                        curve: Curves.easeOutCubic,
                        offset: Offset(0, bubbleIn.value == 1 ? 0 : 0.3),
                        child: AnimatedOpacity(
                          duration: const Duration(milliseconds: 500),
                          opacity: bubbleIn.value,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                padding:
                                    const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                                decoration: BoxDecoration(
                                  color: Theme.of(context).brightness ==
                                          Brightness.dark
                                      ? Colors.white.withValues(alpha: .12)
                                      : const Color(0xd9ffffff),
                                  border:
                                      Border.all(color: Colors.white.withValues(alpha: .9)),
                                  borderRadius: const BorderRadius.only(
                                    topLeft: Radius.circular(20),
                                    topRight: Radius.circular(20),
                                    bottomLeft: Radius.circular(20),
                                    bottomRight: Radius.circular(4),
                                  ),
                                  boxShadow: [
                                    BoxShadow(
                                      color: const Color(0xFF503c78).withValues(alpha: .22),
                                      blurRadius: 20,
                                      offset: const Offset(0, 8),
                                      spreadRadius: -8,
                                    ),
                                  ],
                                ),
                                child: const Text(
                                  'म साथमा छु।',
                                  style: TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w500,
                                    color: SahayakColors.inkSoft,
                                  ),
                                ),
                              ),
                              // .s1-dots
                              const Padding(
                                padding: EdgeInsets.only(left: 6, top: 10),
                                child: TypingDots(),
                              ),
                            ],
                          ),
                        ),
                      ),
                      // .s1-bot-wrap
                      Expanded(
                        child: Center(
                          child: SahayakBot(width: 210),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              // .s1-cta
              Padding(
                padding: const EdgeInsets.fromLTRB(26, 0, 26, 30),
                child: GoPillButton(
                  label: 'सुरु गर्नुहोस्',
                  onTap: () => context.go('/login'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

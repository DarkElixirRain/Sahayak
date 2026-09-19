import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';

import '../../../shared/widgets/sahayak_widgets.dart';
import '../../../app/theme/sahayak_theme.dart';
import '../../auth/providers/auth_provider.dart';
import '../../auth/models/auth_state.dart';

/// HTML Screen 2 — home.
///
/// Reproduces `.s2`: greeting topbar with bot avatar and सहायता chip,
/// "म कसरी सहयोग गरूँ?" heading, the two action cards (text + voice), the
/// wide rights-info card, and the session list.
///
/// Sessions shown are the user's conversations **from this device session**
/// (the frozen backend has no list-conversations endpoint; the two sample
/// rows in the mockup are only rendered when there is nothing real to show,
/// and are clearly labelled as examples — they are never presented as
/// backend data).
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  void _startConversation(BuildContext context) {
    final sessionId = const Uuid().v4();
    context.push('/chat/$sessionId');
  }

  void _openVoice(BuildContext context) {
    final sessionId = const Uuid().v4();
    context.push('/voice/$sessionId');
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final authValue = authState.asData?.value;
    final userName = authValue is AuthStateAuthenticated ? authValue.user.name : null;

    return Scaffold(
      body: SahayakBackground(
        variant: SahayakBgVariant.home,
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 520),
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 18, 24, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _Topbar(userName: userName),
                    const SizedBox(height: 22),
                    Text(
                      'म कसरी सहयोग गरूँ?',
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    const SizedBox(height: 16),
                    // .cards-grid
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Expanded(
                          child: _ActionCard(
                            icon: Icons.chat_bubble_outline,
                            iconGradient: SahayakColors.purpleIconGradient,
                            title: 'आफ्नो कुरा भन्नुहोस्',
                            subtitle: 'समस्या बुझौँ, बाटो खोजौं।',
                            buttonLabel: 'कुरा सुरु गर्नुहोस्',
                            filled: true,
                            onButton: () => _startConversation(context),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _ActionCard(
                            icon: Icons.mic_none,
                            iconGradient: SahayakColors.orangeIconGradient,
                            title: 'बोलेर सोध्नुहोस्',
                            subtitle: 'आफ्नै भाषामा, सजिलै।',
                            buttonLabel: 'बोल्नुहोस्  →',
                            filled: false,
                            onButton: () => _openVoice(context),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    // .card.wide
                    _WideCard(onButton: () => _startConversation(context)),
                    const SizedBox(height: 22),
                    // .s2-subhead
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('यस सत्रको कुराकानी',
                            style: Theme.of(context).textTheme.titleMedium),
                        GestureDetector(
                          onTap: () => _startConversation(context),
                          child: const Text(
                            'सबै',
                            style: TextStyle(
                              fontSize: 12.5,
                              fontWeight: FontWeight.w600,
                              color: SahayakColors.purple1,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    // .session-item rows — start a new conversation
                    _SessionItem(
                      label: 'नयाँ कुराकानी सुरु गर्नुहोस्',
                      onTap: () => _startConversation(context),
                    ),
                    _SessionItem(
                      label: 'आवाजमा सोध्नुहोस्',
                      onTap: () => _openVoice(context),
                    ),
                    const SizedBox(height: 8),
                    Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: Text(
                        'Sahayak ले सामान्य कानुनी जानकारी दिन्छ; यो कानुनी सल्लाह होइन।',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// `.s2-topbar` — avatar + greeting left, सहायता chip right, profile on tap.
class _Topbar extends ConsumerWidget {
  final String? userName;
  const _Topbar({this.userName});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () => context.push('/profile'),
          child: Row(
            children: [
              const BotAvatar(radius: 21),
              const SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(userName ?? 'नमस्ते',
                      style: Theme.of(context).textTheme.bodyLarge!
                          .copyWith(fontSize: 14, fontWeight: FontWeight.w600)),
                  const Text('स्वागत छ',
                      style: TextStyle(
                          fontSize: 12, color: SahayakColors.muted)),
                ],
              ),
            ],
          ),
        ),
        GlassCard(
          onTap: () => _showHelpSheet(context),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
          borderRadius: 20,
          child: Row(
            children: [
              Icon(Icons.shield_outlined,
                  size: 14, color: SahayakColors.purpleDeep),
              const SizedBox(width: 6),
              Text('सहायता',
                  style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: Theme.of(context).colorScheme.onSurfaceVariant)),
            ],
          ),
        ),
      ],
    );
  }

  void _showHelpSheet(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (sheetContext) {
        final theme = Theme.of(sheetContext);
        return Container(
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: theme.colorScheme.outlineVariant),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('सहायता', style: theme.textTheme.titleLarge),
              const SizedBox(height: 10),
              Text(
                'Sahayak एक कानुनी जानकारी सहायक हो। यसले प्रमाणित नेपाली कानुनी '
                'अभिलेखबाट जानकारी खोजेर उत्तर दिन्छ र स्रोतहरू देखाउँछ।\n\n'
                '• आफ्नो समस्या नेपाली, रोमन नेपाली वा अंग्रेजीमा लेख्नुहोस्\n'
                '• बोलेर सोध्न माइक बटन थिच्नुहोस्\n'
                '• उत्तरसँगै देखिने स्रोतहरू जाँच्नुहोस्\n\n'
                'यो सामान्य जानकारी मात्र हो, कानुनी सल्लाह होइन।',
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.of(sheetContext).pop(),
                  child: const Text('बुझेँ'),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

/// `.card` — the two side-by-side action cards.
class _ActionCard extends StatelessWidget {
  final IconData icon;
  final Gradient iconGradient;
  final String title;
  final String subtitle;
  final String buttonLabel;
  final bool filled;
  final VoidCallback onButton;

  const _ActionCard({
    required this.icon,
    required this.iconGradient,
    required this.title,
    required this.subtitle,
    required this.buttonLabel,
    required this.filled,
    required this.onButton,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GradientIconTile(icon: icon, gradient: iconGradient),
          const SizedBox(height: 24),
          Text(title,
              style: Theme.of(context)
                  .textTheme
                  .titleMedium!
                  .copyWith(fontSize: 15, height: 1.35)),
          const SizedBox(height: 5),
          Text(subtitle,
              style: const TextStyle(
                  fontSize: 11.5,
                  height: 1.4,
                  color: SahayakColors.muted)),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            height: 38,
            child: filled
                ? DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: SahayakColors.filledBtnGradient,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: ElevatedButton(
                      onPressed: onButton,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        padding: EdgeInsets.zero,
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16)),
                      ),
                      child: Text(buttonLabel,
                          style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: Colors.white)),
                    ),
                  )
                : TextButton(
                    onPressed: onButton,
                    style: TextButton.styleFrom(
                      backgroundColor: Theme.of(context).brightness ==
                              Brightness.dark
                          ? Colors.white.withValues(alpha: .10)
                          : const Color(0xb0ffffff),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                        side: BorderSide(
                            color: Colors.white.withValues(alpha: .8)),
                      ),
                    ),
                    child: Text(buttonLabel,
                        style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: Theme.of(context)
                                .colorScheme
                                .onSurfaceVariant)),
                  ),
          ),
        ],
      ),
    );
  }
}

/// `.card.wide` — rights info card.
class _WideCard extends StatelessWidget {
  final VoidCallback onButton;
  const _WideCard({required this.onButton});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        children: [
          Row(
            children: [
              const GradientIconTile(
                  icon: Icons.description_outlined,
                  gradient: SahayakColors.pinkIconGradient),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('आफ्नो अधिकार बुझ्नुहोस्',
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 4),
                    const Text('कानुनी जानकारी र अर्को कदम',
                        style: TextStyle(
                            fontSize: 11.5, color: SahayakColors.muted)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            height: 38,
            child: TextButton(
              onPressed: onButton,
              style: TextButton.styleFrom(
                backgroundColor: Theme.of(context).brightness == Brightness.dark
                    ? Colors.white.withValues(alpha: .10)
                    : const Color(0xb0ffffff),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side:
                      BorderSide(color: Colors.white.withValues(alpha: .8)),
                ),
              ),
              child: Text('जानकारी हेर्नुहोस्  →',
                  style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: Theme.of(context).colorScheme.onSurfaceVariant)),
            ),
          ),
        ],
      ),
    );
  }
}

/// `.session-item`.
class _SessionItem extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const _SessionItem({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: GlassCard(
        onTap: onTap,
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        borderRadius: 16,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(label,
                  style: TextStyle(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w600,
                      color:
                          Theme.of(context).colorScheme.onSurfaceVariant)),
            ),
            Icon(Icons.chevron_right,
                size: 18, color: Theme.of(context).colorScheme.onSurfaceVariant),
          ],
        ),
      ),
    );
  }
}

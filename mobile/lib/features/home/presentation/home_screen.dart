import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/demo/demo_data.dart';
import '../../../core/demo/demo_repository.dart';
import '../../../core/theme/app_colors.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final unread = ref.watch(demoRepositoryProvider).unreadNotificationCount;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 18.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildTopBar(context, unread),
                const SizedBox(height: 22),
                const Text(
                  'म कसरी सहयोग गरूँ?',
                  style: TextStyle(
                    fontSize: 23,
                    fontWeight: FontWeight.bold,
                    color: AppColors.ink,
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: _buildActionCard(
                        context,
                        title: 'आफ्नो कुरा भन्नुहोस्',
                        subtitle: 'समस्या बुझौँ, बाटो खोजौं।',
                        iconGradient: AppColors.purpleGradient,
                        icon: Icons.chat_bubble_outline,
                        buttonText: 'कुरा सुरु गर्नुहोस्',
                        isFilledButton: true,
                        onTap: () => context.push('/chat'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildActionCard(
                        context,
                        title: 'बोलेर सोध्नुहोस्',
                        subtitle: 'आफ्नै भाषामा, सजिलै।',
                        iconGradient: const LinearGradient(colors: [AppColors.orange1, AppColors.orange2]),
                        icon: Icons.mic_none,
                        buttonText: 'बोल्नुहोस्  →',
                        isFilledButton: false,
                        onTap: () {
                          context.push('/voice');
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                _buildQuickActions(context),
                const SizedBox(height: 20),
                _buildRecentSection(context),
                const SizedBox(height: 12),
                _buildWideCard(context),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ── Top bar with profile, notifications, settings ─────────────────────────

  Widget _buildTopBar(BuildContext context, int unread) {
    const profile = DemoData.profile;

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        GestureDetector(
          onTap: () => context.push('/profile'),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: AppColors.purpleGradient,
                ),
                child: const Center(
                  child: Text(
                    'बि',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('नमस्ते', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.ink)),
                  Text(profile.name.split(' ').first, style: const TextStyle(fontSize: 12, color: AppColors.muted)),
                ],
              ),
            ],
          ),
        ),
        Row(
          children: [
            GestureDetector(
              onTap: () => context.push('/notifications'),
              child: Stack(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.75),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: Colors.white),
                    ),
                    child: const Icon(Icons.notifications_none, color: AppColors.inkSoft, size: 20),
                  ),
                  if (unread > 0)
                    Positioned(
                      right: 6,
                      top: 6,
                      child: Container(
                        padding: const EdgeInsets.all(3),
                        decoration: const BoxDecoration(
                          color: AppColors.pink1,
                          shape: BoxShape.circle,
                        ),
                        constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
                        child: Text(
                          '$unread',
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            GestureDetector(
              onTap: () => context.push('/settings'),
              child: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.75),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.white),
                ),
                child: const Icon(Icons.settings_outlined, color: AppColors.inkSoft, size: 20),
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ── Quick actions ──────────────────────────────────────────────────────────

  Widget _buildQuickActions(BuildContext context) {
    final actions = <_QuickAction>[
      _QuickAction(label: 'अस्क सहायक', icon: Icons.chat_bubble_outline, route: '/chat'),
      _QuickAction(label: 'आवाज', icon: Icons.mic_none, route: '/voice'),
      _QuickAction(label: 'कानुनी जानकारी', icon: Icons.menu_book_outlined, route: '/search'),
      _QuickAction(label: 'मेरो परामर्श', icon: Icons.folder_outlined, route: '/cases'),
      _QuickAction(label: 'सुरक्षित', icon: Icons.bookmark_border, route: '/saved'),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'द्रुत पहुँच',
          style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.ink),
        ),
        const SizedBox(height: 10),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: actions.map((a) => _buildQuickAction(context, a)).toList(),
        ),
      ],
    );
  }

  Widget _buildQuickAction(BuildContext context, _QuickAction action) {
    return GestureDetector(
      onTap: () => context.push(action.route),
      child: Container(
        width: (MediaQuery.of(context).size.width - 48 - 20) / 3,
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 4),
        decoration: BoxDecoration(
          color: AppColors.cardBg,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.cardBorder),
        ),
        child: Column(
          children: [
            Icon(action.icon, color: AppColors.purple1, size: 22),
            const SizedBox(height: 8),
            Text(
              action.label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppColors.inkSoft,
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Recent / dashboard widgets ─────────────────────────────────────────────

  Widget _buildRecentSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'भर्खरको',
          style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.ink),
        ),
        const SizedBox(height: 10),
        _buildRecentCard(
          context,
          icon: Icons.security,
          gradient: const LinearGradient(colors: [AppColors.purple1, AppColors.purple2]),
          title: DemoData.recentConsultationTitle,
          subtitle: DemoData.recentConsultationAgo,
          route: '/chat',
        ),
        const SizedBox(height: 8),
        _buildRecentCard(
          context,
          icon: Icons.bookmark_border,
          gradient: const LinearGradient(colors: [AppColors.pink1, AppColors.pink2]),
          title: DemoData.savedGuidanceTitle,
          subtitle: DemoData.savedGuidanceAgo,
          route: '/saved',
        ),
        const SizedBox(height: 8),
        _buildRecentCard(
          context,
          icon: Icons.folder_outlined,
          gradient: const LinearGradient(colors: [AppColors.orange1, AppColors.orange2]),
          title: DemoData.recentCaseTitle,
          subtitle: DemoData.recentCaseAgo,
          route: '/cases',
        ),
      ],
    );
  }

  Widget _buildRecentCard(
    BuildContext context, {
    required IconData icon,
    required Gradient gradient,
    required String title,
    required String subtitle,
    required String route,
  }) {
    return GestureDetector(
      onTap: () => context.push(route),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.7),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white),
        ),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                gradient: gradient,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: Colors.white, size: 18),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w600,
                      color: AppColors.inkSoft,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppColors.muted, size: 20),
          ],
        ),
      ),
    );
  }

  // ── Existing components (kept from the original design) ───────────────────

  Widget _buildActionCard(
    BuildContext context, {
    required String title,
    required String subtitle,
    required Gradient iconGradient,
    required IconData icon,
    required String buttonText,
    required bool isFilledButton,
    required VoidCallback onTap,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        border: Border.all(color: AppColors.cardBorder),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: AppColors.ink.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              gradient: iconGradient,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: Colors.white, size: 20),
          ),
          const SizedBox(height: 24),
          Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.ink)),
          const SizedBox(height: 5),
          Text(subtitle, style: const TextStyle(fontSize: 11.5, color: AppColors.muted)),
          const SizedBox(height: 14),
          GestureDetector(
            onTap: onTap,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                gradient: isFilledButton ? AppColors.purpleGradient : null,
                color: isFilledButton ? null : Colors.white.withValues(alpha: 0.7),
                borderRadius: BorderRadius.circular(16),
                border: isFilledButton ? null : Border.all(color: Colors.white),
              ),
              alignment: Alignment.center,
              child: Text(
                buttonText,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: isFilledButton ? Colors.white : AppColors.inkSoft,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWideCard(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push('/search'),
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: AppColors.cardBg,
          border: Border.all(color: AppColors.cardBorder),
          borderRadius: BorderRadius.circular(22),
        ),
        child: Column(
          children: [
            Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(colors: [AppColors.pink1, AppColors.pink2]),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.menu_book, color: Colors.white, size: 18),
                ),
                const SizedBox(width: 12),
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('आफ्नो अधिकार बुझ्नुहोस्', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.ink)),
                    Text('कानुनी जानकारी र अर्को कदम', style: TextStyle(fontSize: 11.5, color: AppColors.muted)),
                  ],
                )
              ],
            ),
            const SizedBox(height: 14),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.7),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white),
              ),
              alignment: Alignment.center,
              child: const Text('जानकारी हेर्नुहोस्  →', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.inkSoft)),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickAction {
  final String label;
  final IconData icon;
  final String route;

  const _QuickAction({required this.label, required this.icon, required this.route});
}
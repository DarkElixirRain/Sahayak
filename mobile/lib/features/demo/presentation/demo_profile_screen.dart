import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/demo/demo_models.dart';
import '../../../core/demo/demo_repository.dart';
import '../../../core/theme/app_colors.dart';
import '../../auth/presentation/auth_provider.dart';

/// Demo user profile screen.
///
/// Long-pressing the avatar resets all local demo data to its initial state
/// (developer-only — not surfaced as a labelled control in the UI).
class DemoProfileScreen extends ConsumerWidget {
  const DemoProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final repo = ref.watch(demoRepositoryProvider);
    final profile = repo.profile;
    final savedCount = repo.savedArticles.length;
    final caseCount = repo.consultations.length;

    return Scaffold(
      backgroundColor: AppColors.bgPage,
      appBar: AppBar(
        title: const Text('प्रोफाइल'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios),
          onPressed: () => context.pop(),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          Center(
            child: GestureDetector(
              onLongPress: () {
                ref.read(demoRepositoryProvider).reset();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('स्थानीय डेटा पुनः सेट गरियो।')),
                );
              },
              child: Container(
                width: 88,
                height: 88,
                decoration: const BoxDecoration(
                  gradient: AppColors.purpleGradient,
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: Text(
                    _initials(profile.name),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 30,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Center(
            child: Text(
              profile.name,
              style: const TextStyle(
                color: AppColors.ink,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(height: 4),
          Center(
            child: Text(
              profile.email,
              style: const TextStyle(color: AppColors.muted, fontSize: 13),
            ),
          ),
          Center(
            child: Text(
              '${profile.location} • ${profile.joinedOn} देखि',
              style: const TextStyle(color: AppColors.muted, fontSize: 12.5),
            ),
          ),
          const SizedBox(height: 16),
          Center(
            child: Text(
              profile.bio,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppColors.inkSoft,
                fontSize: 13,
                height: 1.4,
              ),
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              _StatCard(label: 'सुरक्षित', value: '$savedCount'),
              const SizedBox(width: 12),
              _StatCard(label: 'परामर्श', value: '$caseCount'),
            ],
          ),
          const SizedBox(height: 24),
          const Text(
            'भर्खरको गतिविधि',
            style: TextStyle(
              color: AppColors.ink,
              fontSize: 15,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 10),
          ...repo.activities.map((a) => _ActivityTile(activity: a)),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () async {
              await ref.read(authProvider.notifier).logout();
              if (context.mounted) context.go('/');
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: AppColors.inkSoft,
              side: const BorderSide(color: AppColors.cardBorder),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
            ),
            icon: const Icon(Icons.logout, size: 18),
            label: const Text('लग आउट'),
          ),
        ],
      ),
    );
  }

  String _initials(String name) {
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.isEmpty) return 'S';
    final first = parts.first.isNotEmpty ? parts.first[0] : '';
    final last =
        parts.length > 1 && parts.last.isNotEmpty ? parts.last[0] : '';
    return (first + last).toUpperCase();
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;

  const _StatCard({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.cardBorder),
        ),
        child: Column(
          children: [
            Text(
              value,
              style: const TextStyle(
                color: AppColors.purple1,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: const TextStyle(color: AppColors.muted, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _ActivityTile extends StatelessWidget {
  final DemoActivity activity;

  const _ActivityTile({required this.activity});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.cardBorder),
      ),
      child: Row(
        children: [
          Icon(_iconFor(activity.icon), size: 18, color: AppColors.purple1),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              activity.title,
              style: const TextStyle(
                color: AppColors.inkSoft,
                fontSize: 13.5,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Text(
            activity.timeAgo,
            style: const TextStyle(color: AppColors.muted, fontSize: 11.5),
          ),
        ],
      ),
    );
  }

  IconData _iconFor(IconKey key) {
    switch (key) {
      case IconKey.chat:
        return Icons.chat_bubble_outline;
      case IconKey.search:
        return Icons.search;
      case IconKey.bookmark:
        return Icons.bookmark_border;
      case IconKey.file:
        return Icons.description_outlined;
      case IconKey.mic:
        return Icons.mic_none;
      case IconKey.fraud:
        return Icons.security;
    }
  }
}
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/demo/demo_repository.dart';
import '../../../core/theme/app_colors.dart';

/// Notifications screen with working local read/unread state.
class DemoNotificationsScreen extends ConsumerWidget {
  const DemoNotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final repo = ref.watch(demoRepositoryProvider);
    final notifications = repo.notifications;

    return Scaffold(
      backgroundColor: AppColors.bgPage,
      appBar: AppBar(
        title: const Text('सूचनाहरू'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios),
          onPressed: () => context.pop(),
        ),
        actions: [
          TextButton(
            onPressed: notifications.isEmpty
                ? null
                : () => repo.markAllNotificationsRead(),
            child: const Text(
              'सबै पढेको मान्नुहोस्',
              style: TextStyle(color: AppColors.purple1, fontSize: 12.5),
            ),
          ),
        ],
      ),
      body: notifications.isEmpty
          ? const Center(
              child: Text(
                'कुनै सूचना छैन।',
                style: TextStyle(color: AppColors.muted, fontSize: 14),
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              itemCount: notifications.length,
              itemBuilder: (context, index) {
                final n = notifications[index];
                return GestureDetector(
                  onTap: () => repo.markNotificationRead(n.id),
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: n.read
                          ? Colors.white.withValues(alpha: 0.6)
                          : AppColors.cardBg,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: n.read
                            ? AppColors.cardBorder
                            : AppColors.purple2.withValues(alpha: 0.35),
                      ),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 10,
                          height: 10,
                          margin: const EdgeInsets.only(top: 5),
                          decoration: BoxDecoration(
                            color: n.read ? Colors.transparent : AppColors.purple1,
                            shape: BoxShape.circle,
                            border: n.read
                                ? Border.all(color: AppColors.muted)
                                : null,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                n.message,
                                style: const TextStyle(
                                  color: AppColors.inkSoft,
                                  fontSize: 13.5,
                                  height: 1.4,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                n.timeAgo,
                                style: const TextStyle(
                                  color: AppColors.muted,
                                  fontSize: 11.5,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
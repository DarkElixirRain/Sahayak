import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/demo/demo_data.dart';
import '../../../core/demo/demo_repository.dart';
import '../../../core/theme/app_colors.dart';

/// Full-screen viewer for a local legal guidance article.
class DemoArticleScreen extends ConsumerWidget {
  final String articleId;

  const DemoArticleScreen({super.key, required this.articleId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final article = DemoData.articles.firstWhere(
      (a) => a.id == articleId,
      orElse: () => DemoData.articles.first,
    );
    final repo = ref.watch(demoRepositoryProvider);
    final isSaved = repo.isSaved(article.id);

    return Scaffold(
      backgroundColor: AppColors.bgPage,
      appBar: AppBar(
        title: const Text('कानुनी जानकारी'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios),
          onPressed: () => context.pop(),
        ),
        actions: [
          IconButton(
            onPressed: () => repo.toggleSaved(article.id),
            icon: Icon(
              isSaved ? Icons.bookmark : Icons.bookmark_border,
              color: isSaved ? AppColors.purple1 : AppColors.inkSoft,
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              article.category,
              style: const TextStyle(
                color: AppColors.purple1,
                fontSize: 12.5,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              article.title,
              style: const TextStyle(
                color: AppColors.ink,
                fontSize: 22,
                fontWeight: FontWeight.bold,
                height: 1.3,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              article.updatedAgo,
              style: const TextStyle(color: AppColors.muted, fontSize: 12),
            ),
            const SizedBox(height: 18),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppColors.cardBorder),
              ),
              child: Text(
                article.summary,
                style: const TextStyle(
                  color: AppColors.purple1,
                  fontSize: 14.5,
                  fontWeight: FontWeight.w600,
                  height: 1.4,
                ),
              ),
            ),
            const SizedBox(height: 18),
            Text(
              article.content,
              style: const TextStyle(
                color: AppColors.inkSoft,
                fontSize: 15,
                height: 1.6,
              ),
            ),
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.purple2.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.purple2.withValues(alpha: 0.2)),
              ),
              child: const Text(
                'यो सामान्य कानुनी जानकारी हो। विशेष परिस्थितिका लागि योग्य कानुनी सल्लाह लिनुहोस्।',
                style: TextStyle(
                  color: AppColors.inkSoft,
                  fontSize: 12.5,
                  fontStyle: FontStyle.italic,
                  height: 1.4,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
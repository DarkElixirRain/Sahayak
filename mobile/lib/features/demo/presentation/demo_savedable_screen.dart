import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/demo/demo_models.dart';
import '../../../core/demo/demo_repository.dart';
import '../../../core/theme/app_colors.dart';

/// Shared screen for legal-search mode and saved-guidance mode.
///
/// Modes:
///  - [searchMode] == true  → legal search/explore with local catalog
///  - [searchMode] == false → saved guidance list
class DemoSavedableScreen extends ConsumerStatefulWidget {
  final bool searchMode;

  const DemoSavedableScreen({super.key, required this.searchMode});

  @override
  ConsumerState<DemoSavedableScreen> createState() => _DemoSavedableScreenState();
}

class _DemoSavedableScreenState extends ConsumerState<DemoSavedableScreen> {
  final TextEditingController _controller = TextEditingController();
  List<DemoArticle> _results = [];
  bool _searching = false;
  String? _selectedCategory;

  @override
  void initState() {
    super.initState();
    if (widget.searchMode) {
      _searching = true;
      _runSearch('');
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _runSearch(String query) async {
    setState(() => _searching = true);
    final results = await ref
        .read(demoRepositoryProvider)
        .searchArticles(query);
    if (!mounted) return;
    setState(() {
      _results = results;
      _searching = false;
    });
  }

  void _selectCategory(String category) {
    if (_selectedCategory == category) {
      setState(() => _selectedCategory = null);
      _runSearch(_controller.text);
      return;
    }
    setState(() => _selectedCategory = category);
    _runSearch('$category ${_controller.text}'.trim());
  }

  @override
  Widget build(BuildContext context) {
    if (widget.searchMode) return _buildSearch(context);
    return _buildSaved(context);
  }

  // ── Search mode ───────────────────────────────────────────────────────────

  Widget _buildSearch(BuildContext context) {
    final categories = ref.watch(demoRepositoryProvider).articles
        .map((a) => a.category)
        .toSet()
        .toList();

    return Scaffold(
      backgroundColor: AppColors.bgPage,
      appBar: AppBar(
        title: const Text('कानुनी खोज'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios),
          onPressed: () => context.pop(),
        ),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
            child: TextField(
              controller: _controller,
              textInputAction: TextInputAction.search,
              onSubmitted: _runSearch,
              decoration: InputDecoration(
                hintText: 'खोज्नुहोस्... (जस्तै: bank, जग्गा, ठगी)',
                hintStyle: const TextStyle(color: AppColors.muted, fontSize: 13.5),
                prefixIcon: const Icon(Icons.search, color: AppColors.purple1),
                suffixIcon: _controller.text.isEmpty
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.close, size: 18, color: AppColors.muted),
                        onPressed: () {
                          _controller.clear();
                          _runSearch('');
                        },
                      ),
                filled: true,
                fillColor: Colors.white,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: const BorderSide(color: AppColors.cardBorder),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: const BorderSide(color: AppColors.cardBorder),
                ),
              ),
            ),
          ),
          SizedBox(
            height: 44,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              children: categories.map((cat) {
                final selected = _selectedCategory == cat;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: GestureDetector(
                    onTap: () => _selectCategory(cat),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      decoration: BoxDecoration(
                        color: selected ? AppColors.purple1 : Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: selected ? AppColors.purple1 : AppColors.cardBorder,
                        ),
                      ),
                      child: Text(
                        cat,
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w600,
                          color: selected ? Colors.white : AppColors.inkSoft,
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 4),
          Expanded(
            child: _searching
                ? const Center(child: CircularProgressIndicator(color: AppColors.purple1))
                : _results.isEmpty
                    ? const _EmptyState(
                        icon: Icons.search_off,
                        message: 'कुनै नतिजा भेटिएन। फरक शब्द खोज्ने प्रयास गर्नुहोस्।',
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                        itemCount: _results.length,
                        itemBuilder: (context, index) =>
                            _ArticleTile(article: _results[index]),
                      ),
          ),
        ],
      ),
    );
  }

  // ── Saved mode ────────────────────────────────────────────────────────────

  Widget _buildSaved(BuildContext context) {
    final saved = ref.watch(demoRepositoryProvider).savedArticles;

    return Scaffold(
      backgroundColor: AppColors.bgPage,
      appBar: AppBar(
        title: const Text('सुरक्षित कानुनी जानकारी'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios),
          onPressed: () => context.pop(),
        ),
      ),
      body: saved.isEmpty
          ? const _EmptyState(
              icon: Icons.bookmark_border,
              message: 'सुरक्षित कानुनी जानकारी छैन। कानुनी खोजबाट थप्न सक्नुहुन्छ।',
            )
          : ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              itemCount: saved.length,
              itemBuilder: (context, index) => _ArticleTile(
                article: saved[index],
                showRemove: true,
              ),
            ),
    );
  }
}

// ── Article tile ─────────────────────────────────────────────────────────────

class _ArticleTile extends ConsumerWidget {
  final DemoArticle article;
  final bool showRemove;

  const _ArticleTile({required this.article, this.showRemove = false});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final repo = ref.watch(demoRepositoryProvider);
    final isSaved = repo.isSaved(article.id);
    final isCurrentSaved = showRemove || isSaved;

    return GestureDetector(
      onTap: () => context.push('/article', extra: {'articleId': article.id}),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.cardBg,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppColors.cardBorder),
          boxShadow: [
            BoxShadow(
              color: AppColors.ink.withValues(alpha: 0.04),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    article.category,
                    style: const TextStyle(
                      color: AppColors.purple1,
                      fontSize: 11.5,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    article.title,
                    style: const TextStyle(
                      color: AppColors.ink,
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    article.summary,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppColors.muted,
                      fontSize: 12.5,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            GestureDetector(
              onTap: () => isCurrentSaved
                  ? repo.removeSaved(article.id)
                  : repo.toggleSaved(article.id),
              child: Padding(
                padding: const EdgeInsets.all(6),
                child: Icon(
                  isCurrentSaved ? Icons.bookmark : Icons.bookmark_border,
                  size: 22,
                  color: isCurrentSaved ? AppColors.purple1 : AppColors.muted,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final IconData icon;
  final String message;

  const _EmptyState({required this.icon, required this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 56, color: AppColors.muted.withValues(alpha: 0.6)),
            const SizedBox(height: 12),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.muted, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}
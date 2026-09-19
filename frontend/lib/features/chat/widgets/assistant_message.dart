import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

import '../../../app/theme/sahayak_theme.dart';
import '../../../shared/widgets/sahayak_widgets.dart';
import '../models/chat_models.dart';
import '../../voice/widgets/audio_player_widget.dart';

/// Sahayak assistant turn.
///
/// Renders exactly what the backend returned:
///   * `answer`          → markdown body
///   * `status=no_match` → graceful "no verified provision found" presentation
///   * `citations`       → expandable citation cards (none shown when empty)
///   * `follow_up_questions` → suggestion chips (from the response only)
///   * `disclaimer`      → small italic footer
///   * `audio`           → inline TTS player when present
///
/// Model-internal reasoning is never rendered (the backend does not send it
/// and the UI must never show it).
class AssistantMessage extends StatelessWidget {
  final ConversationMessage message;

  const AssistantMessage({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isNoMatch = message.status == 'no_match' ||
        message.status == 'no_verified_context';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const BotAvatar(radius: 15),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (isNoMatch)
                  _NoMatchCard(content: message.content)
                else
                  GlassCard(
                    padding: const EdgeInsets.all(14),
                    borderRadius: 18,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        MarkdownBody(
                          data: message.content,
                          selectable: true,
                          styleSheet: MarkdownStyleSheet(
                            p: TextStyle(
                              fontSize: 14.5,
                              height: 1.5,
                              color: theme.colorScheme.onSurface,
                            ),
                            listBullet: TextStyle(
                                fontSize: 14,
                                height: 1.5,
                                color: theme.colorScheme.onSurface),
                            strong: TextStyle(
                                fontSize: 14.5,
                                fontWeight: FontWeight.w700,
                                color: theme.colorScheme.onSurface),
                            h1: const TextStyle(
                                fontSize: 17, fontWeight: FontWeight.w700),
                            h2: const TextStyle(
                                fontSize: 15.5, fontWeight: FontWeight.w700),
                            blockquote: TextStyle(
                                fontSize: 13.5,
                                color: theme.colorScheme.onSurfaceVariant),
                            code: TextStyle(
                                fontSize: 13,
                                backgroundColor: theme
                                    .colorScheme.surfaceContainerHighest),
                            codeblockDecoration: BoxDecoration(
                              color:
                                  theme.colorScheme.surfaceContainerHighest,
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                        ),
                        if (message.audio != null &&
                            message.audio!.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 8),
                            child: AudioPlayerWidget(
                                base64Audio: message.audio!),
                          ),
                      ],
                    ),
                  ),
                if (message.citations.isNotEmpty)
                  _Citations(citations: message.citations),
                if (message.disclaimer != null &&
                    message.disclaimer!.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 6, left: 2),
                    child: Text(
                      message.disclaimer!,
                      style: TextStyle(
                        fontSize: 10.5,
                        height: 1.35,
                        color: theme.colorScheme.onSurfaceVariant
                            .withValues(alpha: .8),
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// `.no-match` presentation: amber-tinted card so the user can tell at a
/// glance that this is an honest "couldn't find" answer, not a failure.
class _NoMatchCard extends StatelessWidget {
  final String content;
  const _NoMatchCard({required this.content});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDark
            ? const Color(0xFF4a3a20).withValues(alpha: .35)
            : const Color(0xFFfdf3e3).withValues(alpha: .9),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
            color: const Color(0xFFf5a35a).withValues(alpha: .45)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.search_off, size: 20, color: Color(0xFFc77c22)),
          const SizedBox(width: 10),
          Expanded(
            child: SelectableText(
              content,
              style: const TextStyle(
                  fontSize: 14, height: 1.5, color: SahayakColors.ink),
            ),
          ),
        ],
      ),
    );
  }
}

/// Citation cards: `.citation-card` equivalent — one collapsible card per
/// cited provision, distinct from the answer bubble, with source attribution.
class _Citations extends StatefulWidget {
  final List<Citation> citations;
  const _Citations({required this.citations});

  @override
  State<_Citations> createState() => _CitationsState();
}

class _CitationsState extends State<_Citations> {
  final Set<int> _expanded = {};

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(left: 2, bottom: 4),
            child: Row(
              children: [
                Icon(Icons.menu_book_outlined,
                    size: 12, color: SahayakColors.purpleDeep),
                const SizedBox(width: 4),
                Text(
                  'स्रोतहरू (${widget.citations.length})',
                  style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: SahayakColors.purpleDeep),
                ),
              ],
            ),
          ),
          for (var i = 0; i < widget.citations.length; i++)
            _CitationCard(
              citation: widget.citations[i],
              expanded: _expanded.contains(i),
              onToggle: () => setState(() {
                _expanded.contains(i)
                    ? _expanded.remove(i)
                    : _expanded.add(i);
              }),
            ),
        ],
      ),
    );
  }
}

class _CitationCard extends StatelessWidget {
  final Citation citation;
  final bool expanded;
  final VoidCallback onToggle;

  const _CitationCard({
    required this.citation,
    required this.expanded,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Material(
        color: Colors.transparent,
        child: Ink(
          decoration: BoxDecoration(
            color: isDark
                ? Colors.white.withValues(alpha: .07)
                : Colors.white.withValues(alpha: .85),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
                color: SahayakColors.purple1.withValues(alpha: .35)),
          ),
          child: InkWell(
            borderRadius: BorderRadius.circular(14),
            onTap: onToggle,
            child: Padding(
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: SahayakColors.purple1.withValues(alpha: .12),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          'दफा ${citation.section}',
                          style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: SahayakColors.purpleDeep),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          citation.sectionTitle?.isNotEmpty == true
                              ? citation.sectionTitle!
                              : citation.document,
                          maxLines: expanded ? null : 1,
                          overflow: expanded
                              ? TextOverflow.visible
                              : TextOverflow.ellipsis,
                          style: TextStyle(
                              fontSize: 12.5,
                              fontWeight: FontWeight.w600,
                              color: theme.colorScheme.onSurface),
                        ),
                      ),
                      Icon(
                        expanded
                            ? Icons.keyboard_arrow_up
                            : Icons.keyboard_arrow_down,
                        size: 18,
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ],
                  ),
                  AnimatedSize(
                    duration: const Duration(milliseconds: 180),
                    curve: Curves.easeOut,
                    alignment: Alignment.topLeft,
                    child: expanded
                        ? Padding(
                            padding: const EdgeInsets.only(top: 8),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(citation.document,
                                    style: TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w600,
                                        color: theme
                                            .colorScheme.onSurfaceVariant)),
                                const SizedBox(height: 4),
                                if (citation.provision.isNotEmpty)
                                  Text(citation.provision,
                                      style: TextStyle(
                                          fontSize: 12,
                                          height: 1.45,
                                          color: theme.colorScheme
                                              .onSurfaceVariant)),
                                const SizedBox(height: 6),
                                Row(
                                  children: [
                                    Icon(Icons.verified_outlined,
                                        size: 12,
                                        color: SahayakColors.purpleDeep),
                                    const SizedBox(width: 4),
                                    Expanded(
                                      child: Text(
                                        citation.source,
                                        style: TextStyle(
                                            fontSize: 11,
                                            color: theme.colorScheme
                                                .onSurfaceVariant),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          )
                        : const SizedBox(width: double.infinity),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

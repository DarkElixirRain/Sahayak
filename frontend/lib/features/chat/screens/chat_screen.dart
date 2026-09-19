import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme/sahayak_theme.dart';
import '../../../shared/widgets/sahayak_widgets.dart';
import '../providers/chat_provider.dart';
import '../widgets/assistant_message.dart';
import '../widgets/message_composer.dart';
import '../widgets/user_message.dart';

const double _kContentMaxWidth = 760;

class ChatScreen extends HookConsumerWidget {
  final String sessionId;

  const ChatScreen({super.key, required this.sessionId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final chatState = ref.watch(chatProvider(sessionId));
    final textController = useTextEditingController();
    final scrollController = useScrollController();
    final theme = Theme.of(context);

    ref.listen(chatProvider(sessionId), (previous, next) {
      final data = next.value;
      // Surface send failures as a snackbar.
      if (data?.error != null &&
          data!.error != previous?.value?.error &&
          context.mounted) {
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(
              content: Text(data.error!),
              backgroundColor: theme.colorScheme.error));
        ref.read(chatProvider(sessionId).notifier).clearError();
      }
      // Auto-scroll to bottom when new messages arrive.
      next.whenData((_) {
        if (scrollController.hasClients) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (!scrollController.hasClients) return;
            scrollController.animateTo(
              scrollController.position.maxScrollExtent,
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeOut,
            );
          });
        }
      });
    });

    return Scaffold(
      body: SahayakBackground(
        variant: SahayakBgVariant.voice,
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: _kContentMaxWidth),
              child: Column(
                children: [
                  // Minimal header: back + title + voice shortcut.
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
                    child: Row(
                      children: [
                        FrostedCircleButton(
                          semanticLabel: 'Back',
                          size: 38,
                          onTap: () => context.pop(),
                          child: const Icon(Icons.chevron_left, size: 22),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text('कुराकानी',
                              style: Theme.of(context).textTheme.titleLarge),
                        ),
                        FrostedCircleButton(
                          semanticLabel: 'Ask by voice',
                          size: 38,
                          onTap: () => context.push('/voice/$sessionId'),
                          child: const Icon(Icons.mic_none, size: 20),
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: chatState.when(
                      data: (ui) {
                        final messages = ui.status.messages;
                        return Column(
                          children: [
                            Expanded(
                              child: messages.isEmpty
                                  ? const _EmptyConversation()
                                  : ListView.builder(
                                      controller: scrollController,
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 16, vertical: 12),
                                      itemCount: messages.length + (ui.isSending ? 1 : 0),
                                      itemBuilder: (context, index) {
                                        if (ui.isSending &&
                                            index == messages.length) {
                                          // "Thinking…" placeholder while the
                                          // backend generates (never shows any
                                          // model reasoning).
                                          return Align(
                                            alignment: Alignment.centerLeft,
                                            child: Padding(
                                              padding: const EdgeInsets.only(
                                                  left: 40, top: 6, bottom: 6),
                                              child: GlassCard(
                                                padding: const EdgeInsets
                                                    .symmetric(
                                                    horizontal: 16,
                                                    vertical: 12),
                                                borderRadius: 20,
                                                child: Row(
                                                  mainAxisSize:
                                                      MainAxisSize.min,
                                                  children: [
                                                    const TypingDots(),
                                                    const SizedBox(width: 10),
                                                    Text('सोच्दैछु…',
                                                        style: TextStyle(
                                                            fontSize: 13,
                                                            color: Theme.of(
                                                                    context)
                                                                .colorScheme
                                                                .onSurfaceVariant)),
                                                  ],
                                                ),
                                              ),
                                            ),
                                          );
                                        }
                                        final m = messages[index];
                                        return m.role == 'user'
                                            ? UserMessage(message: m)
                                            : AssistantMessage(message: m);
                                      },
                                    ),
                            ),
                            MessageComposer(
                              controller: textController,
                              isSending: ui.isSending,
                              onSendText: (text) {
                                if (text.trim().isEmpty) return;
                                textController.clear();
                                ref
                                    .read(chatProvider(sessionId).notifier)
                                    .sendMessage(text);
                              },
                              onSendVoice: (path) => ref
                                  .read(chatProvider(sessionId).notifier)
                                  .sendVoiceMessage(path),
                            ),
                          ],
                        );
                      },
                      loading: () => const Center(
                          child: CircularProgressIndicator()),
                      error: (error, stack) => _ChatError(
                        error: error,
                        onRetry: () => ref
                            .read(chatProvider(sessionId).notifier)
                            .loadConversation(),
                      ),
                    ),
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

class _EmptyConversation extends StatelessWidget {
  const _EmptyConversation();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 120,
              height: 120,
              child: Center(
                child: BotAvatar(radius: 34),
              ),
            ),
            const SizedBox(height: 16),
            Text('म कसरी सहयोग गरूँ?',
                textAlign: TextAlign.center,
                style: theme.textTheme.headlineMedium),
            const SizedBox(height: 8),
            Text(
              'आफ्नो कानुनी समस्या नेपाली, रोमन नेपाली वा अंग्रेजीमा लेख्नुहोस्। '
              'Sahayak ले प्रमाणित कानुनी अभिलेखबाट जानकारी खोजी दिन्छ।',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium!
                  .copyWith(color: theme.colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: 16),
            GlassCard(
              padding: const EdgeInsets.all(12),
              borderRadius: 16,
              child: Row(
                children: [
                  const Icon(Icons.info_outline,
                      size: 16, color: SahayakColors.muted),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'यो सामान्य कानुनी जानकारी मात्र हो, कानुनी सल्लाह होइन।',
                      style: theme.textTheme.bodySmall,
                    ),
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

class _ChatError extends StatelessWidget {
  final Object error;
  final VoidCallback onRetry;

  const _ChatError({required this.error, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final message = _friendlyMessage(error);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 32),
            const SizedBox(height: 8),
            Text('कुराकानी लोड गर्न सकिएन।',
                style: Theme.of(context).textTheme.titleMedium,
                textAlign: TextAlign.center),
            const SizedBox(height: 6),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('फेरि प्रयास'),
            ),
          ],
        ),
      ),
    );
  }

  String _friendlyMessage(Object error) {
    if (error is DioException) {
      final inner = error.error;
      if (inner != null) return inner.toString();
      return error.message ?? 'Network error.';
    }
    return error.toString();
  }
}

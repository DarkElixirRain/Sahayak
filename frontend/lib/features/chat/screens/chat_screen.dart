import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

import '../providers/chat_provider.dart';
import '../widgets/message_bubble.dart';
import '../../voice/widgets/voice_record_button.dart';

const int kMaxMessageLength = 2000;
const double _kContentMaxWidth = 840;

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
          ..showSnackBar(
            SnackBar(
              content: Text(data.error!),
              backgroundColor: theme.colorScheme.error,
            ),
          );
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
      appBar: AppBar(
        title: const Text('Sahayak'),
        // Compact subtitle removed - keeps header minimal.
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: _kContentMaxWidth),
            child: chatState.when(
              data: (ui) {
                final messages = ui.status.messages;
                return Column(
                  children: [
                    Expanded(
                      child: messages.isEmpty
                          ? _EmptyConversation()
                          : ListView.builder(
                              controller: scrollController,
                              padding: const EdgeInsets.all(16.0),
                              itemCount: messages.length,
                              itemBuilder: (context, index) =>
                                  MessageBubble(message: messages[index]),
                            ),
                    ),
                    _MessageComposer(
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
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stack) => _ChatError(
                error: error,
                onRetry: () => ref
                    .read(chatProvider(sessionId).notifier)
                    .loadConversation(),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _EmptyConversation extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.balance, size: 40, color: theme.colorScheme.primary),
            const SizedBox(height: 12),
            Text(
              'How can Sahayak help you?',
              textAlign: TextAlign.center,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Describe your legal situation or ask a question in '
              'Nepali, Romanized Nepali, or English.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 16),
            Card(
              color: theme.colorScheme.surfaceContainerHighest,
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Row(
                  children: [
                    Icon(
                      Icons.info_outline,
                      size: 16,
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Sahayak provides general legal information and '
                        'cannot replace a qualified lawyer.',
                        style: theme.textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MessageComposer extends HookWidget {
  final TextEditingController controller;
  final bool isSending;
  final ValueChanged<String> onSendText;
  final ValueChanged<String> onSendVoice;

  const _MessageComposer({
    required this.controller,
    required this.isSending,
    required this.onSendText,
    required this.onSendVoice,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasText = useState(false);

    useEffect(() {
      void listener() {
        final value = controller.text.trim().isNotEmpty;
        if (value != hasText.value) hasText.value = value;
      }

      controller.addListener(listener);
      return () => controller.removeListener(listener);
    }, [controller]);

    final canSend = hasText.value && !isSending;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(top: BorderSide(color: theme.dividerColor)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          VoiceRecordButton(
            enabled: !isSending,
            onRecordingComplete: onSendVoice,
          ),
          const SizedBox(width: 6),
          Expanded(
            child: TextField(
              controller: controller,
              enabled: !isSending,
              minLines: 1,
              maxLines: 4,
              maxLength: kMaxMessageLength,
              textInputAction: TextInputAction.newline,
              decoration: InputDecoration(
                hintText: 'Type your message…',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 10,
                ),
              ),
            ),
          ),
          const SizedBox(width: 6),
          isSending
              ? const Padding(
                  padding: EdgeInsets.all(8),
                  child: SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                )
              : IconButton(
                  tooltip: 'Send message',
                  onPressed: canSend ? () => onSendText(controller.text) : null,
                  icon: Icon(
                    Icons.send,
                    color: canSend
                        ? theme.colorScheme.primary
                        : theme.disabledColor,
                    size: 20,
                  ),
                ),
        ],
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
            Text(
              'Could not load this conversation.',
              style: Theme.of(context).textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 6),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
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
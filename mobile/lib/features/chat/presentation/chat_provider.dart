import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../../../core/demo/demo_config.dart';
import '../../../core/demo/demo_repository.dart';
import '../../../core/network/api_client.dart';
import '../data/chat_repository.dart';
import '../../../shared/models/chat_models.dart';

final apiClientProvider = Provider((ref) => ApiClient());
final chatRepositoryProvider = Provider((ref) => ChatRepository(
      ref.watch(apiClientProvider),
      demo: ref.watch(demoRepositoryProvider),
    ));

final chatListProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final repository = ref.watch(chatRepositoryProvider);
  return await repository.getChats();
});

final chatProvider = NotifierProvider<ChatNotifier, ChatState>(ChatNotifier.new);

class ChatState {
  final List<ChatMessage> messages;
  final bool isLoading;
  final String? error;
  final String chatId;

  ChatState({
    required this.messages,
    required this.isLoading,
    this.error,
    required this.chatId,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isLoading,
    String? error,
    String? chatId,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      chatId: chatId ?? this.chatId,
    );
  }
}

class ChatNotifier extends Notifier<ChatState> {
  late final ChatRepository _repository;
  final _uuid = const Uuid();

  @override
  ChatState build() {
    _repository = ref.watch(chatRepositoryProvider);
    final messages = DemoConfig.demoMode
        ? ref.watch(demoRepositoryProvider).initialChatMessages()
        : <ChatMessage>[];
    return ChatState(
      messages: messages,
      isLoading: false,
      chatId: _uuid.v4(),
    );
  }

  void startNewChat() {
    final messages = DemoConfig.demoMode
        ? ref.read(demoRepositoryProvider).initialChatMessages()
        : <ChatMessage>[];
    state = ChatState(
      messages: messages,
      isLoading: false,
      chatId: _uuid.v4(),
    );
  }

  Future<void> loadHistory(String chatId) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final history = await _repository.getChatHistory(chatId);
      state = state.copyWith(
        messages: history,
        chatId: chatId,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to load history: $e',
      );
    }
  }

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;
    if (state.isLoading) return;

    final userMessage = ChatMessage(
      id: _uuid.v4(),
      content: text,
      isUser: true,
      timestamp: DateTime.now(),
    );

    state = state.copyWith(
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null,
    );

    try {
      final response = await _repository.sendQuery(text, chatId: state.chatId);
      
      final aiMessage = ChatMessage(
        id: _uuid.v4(),
        content: response.text,
        isUser: false,
        timestamp: DateTime.now(),
        sources: response.sources,
        structuredAnswer: response.structuredAnswer,
        audioUrl: response.audioUrl,
      );

      state = state.copyWith(
        messages: [...state.messages, aiMessage],
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString().replaceAll('Exception: ', ''),
      );
    }
  }
}

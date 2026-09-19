import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../data/chat_repository.dart';
import '../models/chat_models.dart';

part 'chat_provider.g.dart';

/// UI state for a single conversation.
///
/// Kept as a small hand-written immutable class (not freezed) to avoid extra
/// codegen for three fields.
class ChatUiState {
  const ChatUiState({
    required this.status,
    this.isSending = false,
    this.error,
  });

  final ConversationStatus status;
  final bool isSending;
  final String? error;

  ChatUiState copyWith({
    ConversationStatus? status,
    bool? isSending,
    String? error,
    bool clearError = false,
  }) {
    return ChatUiState(
      status: status ?? this.status,
      isSending: isSending ?? this.isSending,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

ConversationStatus _emptyStatus(String sessionId) => ConversationStatus(
  sessionId: sessionId,
  status: 'active',
  language: 'nepali',
  messageCount: 0,
  startedAt: DateTime.now().toUtc().toIso8601String(),
  messages: const [],
);

@riverpod
class ChatNotifier extends _$ChatNotifier {
  late ChatRepository _repository;

  @override
  FutureOr<ChatUiState> build(String sessionId) async {
    _repository = ref.watch(chatRepositoryProvider);
    try {
      final status = await _repository.getConversationStatus(sessionId);
      return ChatUiState(status: status);
    } on DioException catch (e) {
      // A brand-new session does not exist on the backend yet: a 404 is a
      // normal "empty conversation", anything else is a real failure.
      if (e.response?.statusCode == 404) {
        return ChatUiState(status: _emptyStatus(sessionId));
      }
      rethrow;
    }
  }

  Future<void> loadConversation() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      try {
        final status = await _repository.getConversationStatus(sessionId);
        return ChatUiState(status: status);
      } on DioException catch (e) {
        if (e.response?.statusCode == 404) {
          return ChatUiState(status: _emptyStatus(sessionId));
        }
        rethrow;
      }
    });
  }

  Future<void> sendMessage(String text) async {
    final current = state.value;
    final trimmed = text.trim();
    if (current == null || current.isSending || trimmed.isEmpty) return;

    final optimistic = ConversationMessage(role: 'user', content: trimmed);
    final sendingStatus = current.status.copyWith(
      messages: [...current.status.messages, optimistic],
    );
    state = AsyncData(
      ChatUiState(status: sendingStatus, isSending: true),
    );

    try {
      final response = await _repository.sendMessage(sessionId, trimmed);
      final latest = state.value ?? current;
      final botMessage = ConversationMessage(
        role: 'assistant',
        content: response.answer,
        audio: response.audio,
        citations: response.citations,
        grounded: response.grounded,
        status: response.status,
        disclaimer: response.disclaimer,
      );
      state = AsyncData(
        ChatUiState(
          status: latest.status.copyWith(
            messages: [...latest.status.messages, botMessage],
          ),
          isSending: false,
        ),
      );
    } catch (e) {
      state = AsyncData(
        current.copyWith(isSending: false, error: _messageFor(e)),
      );
    }
  }

  Future<void> sendVoiceMessage(String audioFilePath) async {
    final current = state.value;
    if (current == null || current.isSending) return;

    const voiceMessage = ConversationMessage(
      role: 'user',
      content: 'Voice message',
    );
    final sendingStatus = current.status.copyWith(
      messages: [...current.status.messages, voiceMessage],
    );
    state = AsyncData(
      ChatUiState(status: sendingStatus, isSending: true),
    );

    try {
      final response = await _repository.sendVoiceMessage(
        sessionId,
        audioFilePath,
      );
      final latest = state.value ?? current;
      final botMessage = ConversationMessage(
        role: 'assistant',
        content: response.answer,
        audio: response.audio,
        citations: response.citations,
        grounded: response.grounded,
        status: response.status,
        disclaimer: response.disclaimer,
      );
      state = AsyncData(
        ChatUiState(
          status: latest.status.copyWith(
            messages: [...latest.status.messages, botMessage],
          ),
          isSending: false,
        ),
      );
    } catch (e) {
      state = AsyncData(
        current.copyWith(isSending: false, error: _messageFor(e)),
      );
    }
  }

  void clearError() {
    final current = state.value;
    if (current == null || current.error == null) return;
    state = AsyncData(current.copyWith(clearError: true));
  }

  String _messageFor(Object error) {
    final inner = error is DioException ? error.error : error;
    if (inner is Exception) return inner.toString();
    return error.toString();
  }
}

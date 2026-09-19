import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../models/chat_models.dart';

final chatRepositoryProvider = Provider<ChatRepository>((ref) {
  return ChatRepository(ref.watch(dioClientProvider));
});

class ChatRepository {
  final Dio _dio;

  ChatRepository(this._dio);

  Future<ConversationStatus> getConversationStatus(String sessionId) async {
    final response = await _dio.get('/api/conversations/$sessionId');
    return ConversationStatus.fromJson(response.data);
  }

  Future<ConversationResponse> sendMessage(
    String sessionId,
    String message,
  ) async {
    final response = await _dio.post(
      '/api/conversations/$sessionId/messages',
      data: {'message': message},
    );
    return ConversationResponse.fromJson(response.data);
  }

  Future<ConversationResponse> sendVoiceMessage(
    String sessionId,
    String audioFilePath,
  ) async {
    final formData = FormData.fromMap({
      'audio': await MultipartFile.fromFile(
        audioFilePath,
        filename: 'audio.wav',
      ),
    });

    final response = await _dio.post(
      '/api/conversations/$sessionId/voice',
      data: formData,
    );
    return ConversationResponse.fromJson(response.data);
  }
}

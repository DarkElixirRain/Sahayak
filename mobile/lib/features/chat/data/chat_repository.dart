import 'package:dio/dio.dart';
import '../../../core/demo/demo_config.dart';
import '../../../core/demo/demo_repository.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/models/chat_models.dart';

class ChatRepository {
  final ApiClient _apiClient;
  final DemoRepository _demo;

  ChatRepository(this._apiClient, {DemoRepository? demo})
      : _demo = demo ?? DemoRepository();

  Future<List<Map<String, dynamic>>> getChats() async {
    if (DemoConfig.demoMode) {
      await Future.delayed(DemoConfig.responseDelay);
      return _demo.chatList();
    }
    try {
      final response = await _apiClient.dio.get('/chats');
      if (response.statusCode == 200) {
        return List<Map<String, dynamic>>.from(response.data);
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  Future<List<ChatMessage>> getChatHistory(String chatId) async {
    if (DemoConfig.demoMode) {
      await Future.delayed(DemoConfig.responseDelay);
      return _demo.initialChatMessages();
    }
    try {
      final response = await _apiClient.dio.get('/chat/$chatId');
      if (response.statusCode == 200) {
        final data = response.data as List;
        return data.map((e) => ChatMessage(
          id: e['id'] ?? '',
          content: e['content'] ?? '',
          isUser: e['role'] == 'user',
          timestamp: DateTime.parse(e['timestamp'] ?? DateTime.now().toIso8601String()),
        )).toList();
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  Future<QueryResponse> sendQuery(String query, {String? chatId}) async {
    if (DemoConfig.demoMode) {
      return _demo.answerQuery(query);
    }
    try {
      final payload = {
        "query": query,
        "k": 5, // retrieve top 5 context chunks
        "stream_response": false,
        "schema": {
          "type": "object",
          "properties": {
            "response_type": {
              "type": "string",
              "enum": ["casual", "legal_clarification", "legal_answer"]
            },
            "message": {"type": "string"},
            "summary": {"type": "string"},
            "issue": {"type": "string"},
            "applicable_laws": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "act_name": {"type": "string"},
                  "section": {"type": "string"},
                  "explanation": {"type": "string"},
                  "source_id": {"type": "string"}
                },
                "required": ["act_name", "section", "explanation", "source_id"]
              }
            },
            "explanation": {"type": "string"},
            "next_steps": {"type": "array", "items": {"type": "string"}},
            "clarifying_questions": {"type": "array", "items": {"type": "string"}}
          },
          "required": ["response_type", "message"]
        }
      };
      
      if (chatId != null) {
        payload["chat_id"] = chatId;
      }

      final response = await _apiClient.dio.post(
        '/query',
        data: payload,
      );

      if (response.statusCode == 200) {
        return QueryResponse.fromJson(response.data);
      } else {
        throw Exception('Failed to send query: ${response.statusCode}');
      }
    } on DioException catch (e) {
      if (e.response?.statusCode == 429) {
        throw Exception('अहिले धेरै अनुरोधहरू भइरहेका छन्। कृपया केही क्षणपछि फेरि प्रयास गर्नुहोस्।');
      } else if (e.response?.statusCode == 401) {
        throw Exception('Sahayak सेवा अहिले उपलब्ध छैन। (Auth error)');
      }
      throw Exception('Sahayak सेवा अहिले उपलब्ध छैन। कृपया केही समयपछि फेरि प्रयास गर्नुहोस्।');
    } catch (e) {
      throw Exception('तपाईंको प्रश्नसँग प्रत्यक्ष रूपमा मेल खाने प्रमाणित कानुनी स्रोत हाल फेला परेन। थप विवरण दिनुहोस् ताकि थप खोज गर्न सकियोस्।');
    }
  }
}

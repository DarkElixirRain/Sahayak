import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/chat/models/chat_models.dart';

void main() {
  group('ConversationResponse', () {
    test('parses real backend payload', () {
      final json = {
        'answer': 'Test answer',
        'citations': [
          {
            'document': 'Muluki Dewani Sanhita 2074',
            'section': 'Section 141',
            'provision': 'Provision text',
            'source': 'Nepal Law Commission',
            'score': 0.85,
            'source_url': 'https://example.com',
          },
        ],
        'follow_up_questions': [
          {'question': 'What type of matter?', 'reason': 'missing_matter_type'},
        ],
        'needs_clarification': true,
        'confidence': 'low',
        'status': 'no_match',
        'grounded': false,
        'generation': 'none',
        'disclaimer': 'Not legal advice.',
        'llm_provider': null,
        'llm_model': null,
        'llm_error': null,
        'retrieval_status': 'no_match',
        'retrieval_total_found': 0,
        'unverified_match_count': 0,
        'search_terms': ['hello'],
        'audio': null,
      };

      final response = ConversationResponse.fromJson(json);

      expect(response.answer, 'Test answer');
      expect(response.citations.length, 1);
      expect(response.citations[0].document, 'Muluki Dewani Sanhita 2074');
      expect(response.citations[0].sourceUrl, 'https://example.com');
      expect(response.citations[0].score, 0.85);
      expect(response.followUpQuestions.length, 1);
      expect(response.followUpQuestions[0].question, 'What type of matter?');
      expect(response.needsClarification, true);
      expect(response.grounded, false);
      expect(response.disclaimer, 'Not legal advice.');
      expect(response.searchTerms, ['hello']);
      expect(response.audio, isNull);
    });

    test('parses minimal payload with defaults', () {
      final json = <String, dynamic>{
        'answer': 'Simple answer',
      };

      final response = ConversationResponse.fromJson(json);

      expect(response.answer, 'Simple answer');
      expect(response.citations, isEmpty);
      expect(response.followUpQuestions, isEmpty);
      expect(response.needsClarification, false);
      expect(response.confidence, 'low');
      expect(response.status, 'answered');
      expect(response.grounded, false);
      expect(response.generation, 'none');
    });

    test('parses response with audio', () {
      final json = <String, dynamic>{
        'answer': 'Audio response',
        'audio': 'SUQzBAAAAAAAI1RTU0UAAAAPAAADSTBSU0UAAA==',
      };

      final response = ConversationResponse.fromJson(json);

      expect(response.audio, isNotNull);
      expect(response.audio!.startsWith('SUQz'), true);
    });
  });

  group('ConversationStatus', () {
    test('parses real backend status payload', () {
      final json = {
        'session_id': '550e8400-e29b-41d4-a716-446655440000',
        'status': 'active',
        'language': 'nepali',
        'message_count': 2,
        'started_at': '2026-09-19T07:49:59.424218+00:00',
        'messages': [
          {'role': 'user', 'content': 'hello', 'created_at': '2026-09-19T07:50:01.057250+00:00'},
          {'role': 'assistant', 'content': 'I could not find...'},
        ],
      };

      final status = ConversationStatus.fromJson(json);

      expect(status.sessionId, '550e8400-e29b-41d4-a716-446655440000');
      expect(status.status, 'active');
      expect(status.language, 'nepali');
      expect(status.messageCount, 2);
      expect(status.messages.length, 2);
      expect(status.messages[0].role, 'user');
      expect(status.messages[0].content, 'hello');
      expect(status.messages[1].role, 'assistant');
    });

    test('defaults for empty session', () {
      final json = <String, dynamic>{
        'session_id': 'test-id',
        'status': 'active',
      };

      final status = ConversationStatus.fromJson(json);

      expect(status.messageCount, 0);
      expect(status.messages, isEmpty);
      expect(status.language, 'nepali');
    });
  });

  group('ConversationMessage', () {
    test('parses message with optional fields', () {
      final json = {
        'role': 'assistant',
        'content': 'Answer text',
        'created_at': '2026-09-19T07:50:03.422789+00:00',
        'audio': null,
        'citations': [],
        'grounded': true,
        'status': 'answered',
        'disclaimer': 'Not legal advice.',
      };

      final msg = ConversationMessage.fromJson(json);

      expect(msg.role, 'assistant');
      expect(msg.content, 'Answer text');
      expect(msg.createdAt, isNotNull);
      expect(msg.grounded, true);
      expect(msg.disclaimer, 'Not legal advice.');
    });

    test('parses minimal user message', () {
      final json = {
        'role': 'user',
        'content': 'hello',
      };

      final msg = ConversationMessage.fromJson(json);

      expect(msg.role, 'user');
      expect(msg.content, 'hello');
      expect(msg.audio, isNull);
      expect(msg.citations, isEmpty);
      expect(msg.grounded, false);
    });
  });

  group('Citation', () {
    test('parses citation from backend', () {
      final json = {
        'document': 'Muluki Dewani Sanhita',
        'section': 'Section 141',
        'provision': 'Theft provisions',
        'source': 'Nepal Law Commission',
        'score': 0.85,
        'source_url': 'https://example.com/law',
      };

      final citation = Citation.fromJson(json);

      expect(citation.document, 'Muluki Dewani Sanhita');
      expect(citation.section, 'Section 141');
      expect(citation.sourceUrl, 'https://example.com/law');
      expect(citation.score, 0.85);
    });
  });
}

import 'package:flutter_test/flutter_test.dart';
import 'package:sahayak_app/shared/models/chat_models.dart';

void main() {
  group('StructuredLegalAnswer parsing', () {
    test('parses correctly with well-formed applicable_laws objects', () {
      final json = {
        'response_type': 'legal_answer',
        'message': 'Here is the answer',
        'summary': 'Summary text',
        'issue': 'Issue text',
        'applicable_laws': [
          {
            'act_name': 'Act 1',
            'section': 'Section 1',
            'explanation': 'Explanation 1',
            'source_id': 'Source 1'
          }
        ],
        'explanation': 'Explanation text',
        'next_steps': ['Step 1', 'Step 2'],
        'clarifying_questions': ['Question 1']
      };

      final answer = StructuredLegalAnswer.fromJson(json);

      expect(answer.responseType, 'legal_answer');
      expect(answer.message, 'Here is the answer');
      expect(answer.summary, 'Summary text');
      expect(answer.issue, 'Issue text');
      expect(answer.applicableLaws.length, 1);
      expect(answer.applicableLaws.first.actName, 'Act 1');
      expect(answer.applicableLaws.first.section, 'Section 1');
      expect(answer.explanation, 'Explanation text');
      expect(answer.nextSteps.length, 2);
      expect(answer.clarifyingQuestions.length, 1);
    });

    test('parses correctly with string applicable_laws (regression test)', () {
      final json = {
        'response_type': 'legal_answer',
        'message': 'Answer',
        'summary': 'Summary text',
        'issue': 'Issue text',
        'applicable_laws': [
          'Some Act String instead of object'
        ],
        'explanation': 'Explanation text',
        'next_steps': [],
        'clarifying_questions': []
      };

      final answer = StructuredLegalAnswer.fromJson(json);

      expect(answer.applicableLaws.length, 1);
      // The parser maps a string to the 'actName' field
      expect(answer.applicableLaws.first.actName, 'Some Act String instead of object');
      expect(answer.applicableLaws.first.section, '');
    });

    test('handles missing or null fields gracefully', () {
      final json = {
        'response_type': 'casual',
        'message': 'Hello'
        // everything else missing
      };

      final answer = StructuredLegalAnswer.fromJson(json);
      
      expect(answer.responseType, 'casual');
      expect(answer.message, 'Hello');
      expect(answer.summary, '');
    });

    test('tolerates empty applicable_laws', () {
      final json = {
        'summary': 'Summary text',
        'issue': 'Issue text',
        'applicable_laws': [],
        'explanation': 'Explanation text',
        'next_steps': [],
        'clarifying_questions': []
      };

      final answer = StructuredLegalAnswer.fromJson(json);

      expect(answer.applicableLaws, isEmpty);
    });
  });

  group('QueryResponse parsing', () {
    test('parses JSON payload robustly and uses fallback', () {
      final jsonPayload = {
        'completion': {
          'summary': 'Summary',
          'issue': 'Issue',
          'applicable_laws': [],
          'explanation': 'Exp',
          'next_steps': [],
          'clarifying_questions': []
        },
        'sources': [],
        'finish_reason': 'stop'
      };

      final response = QueryResponse.fromJson(jsonPayload);

      expect(response.structuredAnswer, isNotNull);
      expect(response.structuredAnswer!.summary, 'Summary');
      // Verify the text is valid JSON string
      expect(response.text.contains('"summary":"Summary"'), isTrue);
    });

    test('parses plain text correctly', () {
      final jsonPayload = {
        'completion': 'Just plain text',
        'sources': [],
        'finish_reason': 'stop'
      };

      final response = QueryResponse.fromJson(jsonPayload);

      expect(response.structuredAnswer, isNull);
      expect(response.text, 'Just plain text');
    });

    test('parses audio_url when present', () {
      final jsonPayload = {
        'completion': 'Just plain text',
        'sources': [],
        'finish_reason': 'stop',
        'audio_url': '/audio/dummy-response'
      };

      final response = QueryResponse.fromJson(jsonPayload);

      expect(response.audioUrl, '/audio/dummy-response');
    });

    test('audio_url is null when absent', () {
      final jsonPayload = {
        'completion': 'Just plain text',
        'sources': [],
        'finish_reason': 'stop'
      };

      final response = QueryResponse.fromJson(jsonPayload);

      expect(response.audioUrl, isNull);
    });
  });
}

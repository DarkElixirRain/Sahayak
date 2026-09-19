import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/chat/models/chat_models.dart';

void main() {
  group('Citation extended fields', () {
    test('parses full backend citation payload', () {
      final json = {
        'document': 'मुलुकी देवानी संहिता, २०७४',
        'document_id': 'abc',
        'section': '620',
        'section_title': 'अचल सम्पत्तिको लिज करार सम्बन्धी विशेष व्यवस्था',
        'provision': 'कसैले पनि स्वामित्ववालाको लिखित सहमति…',
        'source': 'नेपाल कानून आयोग (Nepal Law Commission)',
        'source_url': 'https://lawcommission.gov.np/…',
        'score': 0.66,
        'is_verified': true,
        'currentness_status': 'current',
      };

      final c = Citation.fromJson(json);

      expect(c.document, 'मुलुकी देवानी संहिता, २०७४');
      expect(c.section, '620');
      expect(c.sectionTitle, 'अचल सम्पत्तिको लिज करार सम्बन्धी विशेष व्यवस्था');
      expect(c.isVerified, true);
      expect(c.currentnessStatus, 'current');
      expect(c.score, 0.66);
    });

    test('defaults for minimal citation payload', () {
      final json = {
        'document': 'Doc',
        'section': '1',
        'provision': 'Text',
        'source': 'Src',
        'score': 0.5,
      };

      final c = Citation.fromJson(json);

      expect(c.sectionTitle, isNull);
      expect(c.isVerified, false);
      expect(c.currentnessStatus, 'unknown');
    });

    test('Devanagari text round-trips without corruption', () {
      const devanagari = 'मेरो भाइले मेरो जग्गा कब्जा गरेको छ।';
      final msg = ConversationMessage(role: 'user', content: devanagari);
      expect(msg.content, devanagari);
    });
  });

  group('status-aware UI flags', () {
    test('no_match status is recognized', () {
      final json = <String, dynamic>{'answer': 'x', 'status': 'no_match'};
      expect(ConversationResponse.fromJson(json).status, 'no_match');
    });

    test('greeting status is recognized', () {
      final json = <String, dynamic>{'answer': 'नमस्ते!', 'status': 'greeting'};
      expect(ConversationResponse.fromJson(json).status, 'greeting');
    });
  });
}

import 'package:flutter_test/flutter_test.dart';

import 'package:sahayak_app/core/demo/demo_assistant_service.dart';
import 'package:sahayak_app/core/demo/demo_config.dart';

void main() {
  const service = DemoAssistantService();

  group('DemoAssistantService scenario matching', () {
    test('Nepali bank OTP call → bankOtP scenario', () {
      final r = service.answer('मेरो बैंकबाट फोन आयो र OTP माग्यो।');
      expect(r.structuredAnswer?.issue, contains('OTP'));
      expect(r.structuredAnswer?.nextSteps, isNotEmpty);
    });

    test('OTP already given → bankOtpGiven scenario', () {
      final r = service.answer('मैले OTP दिइसकेँ अब के गर्ने?');
      expect(
        r.structuredAnswer?.issue,
        contains('साझा भइसकेको'),
      );
    });

    test('Online fraud (Devanagari) → onlineFraud scenario', () {
      final r = service.answer('मलाई अनलाइन ठगी भयो।');
      expect(r.structuredAnswer?.issue, contains('अनलाइन ठगी'));
    });

    test('Land dispute → land scenario', () {
      final r = service.answer('जग्गाको विषयमा विवाद भयो।');
      expect(r.structuredAnswer?.issue, contains('जग्गा'));
    });

    test('Police complaint → police scenario', () {
      final r = service.answer('प्रहरीमा उजुरी कसरी दिने?');
      expect(r.structuredAnswer?.issue, contains('प्रहरी उजुरी'));
    });

    test('Threat → threat scenario', () {
      final r = service.answer('मलाई धम्की दिइरहेको छ।');
      expect(r.structuredAnswer?.issue, contains('धम्की'));
    });

    test('Family dispute → family scenario', () {
      final r = service.answer('घरमा झगडा भयो।');
      expect(r.structuredAnswer?.issue, contains('घरायसी विवाद'));
    });

    test('Romanized Nepali bank OTP call → bankOtP scenario', () {
      final r = service.answer('mero bank bata phone aayo OTP magyo');
      expect(r.structuredAnswer?.issue, contains('OTP'));
    });

    test('Romanized Nepali fraud → onlineFraud scenario', () {
      final r = service.answer('malai online thagi bhayo');
      expect(r.structuredAnswer?.issue, contains('अनलाइन ठगी'));
    });

    test('English land dispute → land scenario', () {
      final r = service.answer('jagga ko dispute cha');
      expect(r.structuredAnswer?.issue, contains('जग्गा'));
    });

    test('English help request → generalHelp scenario', () {
      final r = service.answer('I need legal help.');
      expect(r.structuredAnswer?.responseType, 'legal_clarification');
    });

    test('Divorce (Devanagari) → divorce scenario', () {
      final r = service.answer('मलाई divorce चाहिएको छ।');
      expect(r.structuredAnswer?.issue, contains('सम्बन्ध विच्छेद'));
    });

    test('Divorce (Devanagari spelled) → divorce scenario', () {
      final r = service.answer('डिभोर्स कसरी गर्ने?');
      expect(r.structuredAnswer?.issue, contains('सम्बन्ध विच्छेद'));
    });

    test('Divorce (Devanagari form) → divorce scenario', () {
      final r = service.answer('डिभोर्स गर्न चाहन्छु।');
      expect(r.structuredAnswer?.issue, contains('सम्बन्ध विच्छेद'));
    });

    test('Divorce (husband-wife English) → divorce, not family', () {
      final r = service.answer('मेरो श्रीमतीसँग divorce गर्न चाहन्छु।');
      expect(r.structuredAnswer?.issue, contains('सम्बन्ध विच्छेद'));
    });

    test('Divorce (romanized) → divorce scenario', () {
      final r = service.answer('divorce ko process k ho');
      expect(r.structuredAnswer?.issue, contains('सम्बन्ध विच्छेद'));
    });

    test('Divorce (Nepali-English) → divorce scenario, not family', () {
      final r = service.answer('मलाई divorce को बारेमा जानकारी चाहन्छु।');
      expect(r.structuredAnswer?.issue, contains('सम्बन्ध विच्छेद'));
    });

    test('Unrecognised input → fallback clarification', () {
      final r = service.answer('आज मौसम कस्तो छ?');
      expect(r.structuredAnswer?.responseType, 'legal_clarification');
    });

    test('Empty input → fallback clarification', () {
      final r = service.answer('');
      expect(r.structuredAnswer?.responseType, 'legal_clarification');
    });
  });

  group('DemoAssistantService response shape', () {
    test('always returns local demo audio asset for offline playback', () {
      final r = service.answer('प्रहरीमा उजुरी कसरी दिने?');
      expect(r.audioUrl, DemoConfig.demoAudioAsset);
    });

    test('legal answers carry next steps and a clarifying question', () {
      final r = service.answer('मलाई अनलाइन ठगी भयो।');
      expect(r.structuredAnswer?.nextSteps, isNotEmpty);
      expect(r.structuredAnswer?.clarifyingQuestions, isNotEmpty);
    });

    test('never fabricates a real-world action', () {
      final r = service.answer('मलाई अनलाइन ठगी भयो।');
      final text = r.text.toLowerCase();
      expect(text.contains('उजुरी दर्ता भयो'), isFalse);
      expect(text.contains('filed'), isFalse);
      expect(text.contains('complaint registered'), isFalse);
    });
  });
}
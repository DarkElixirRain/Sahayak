import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/chat/models/chat_models.dart';
import 'package:frontend/features/chat/widgets/assistant_message.dart';
import 'package:frontend/features/chat/widgets/user_message.dart';

ConversationMessage _assistant({
  String status = 'answered',
  List<Citation> citations = const [],
}) =>
    ConversationMessage(
      role: 'assistant',
      content: 'सम्पत्ति कानून भन्नाले…',
      status: status,
      citations: citations,
      disclaimer: 'यो सामान्य कानूनी जानकारी मात्र हो।',
    );

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

void main() {
  group('UserMessage', () {
    testWidgets('renders Devanagari text', (tester) async {
      await tester.pumpWidget(_wrap(const UserMessage(
        message: ConversationMessage(
            role: 'user', content: 'मेरो भाइले मेरो जग्गा कब्जा गरेको छ।'),
      )));

      expect(find.text('मेरो भाइले मेरो जग्गा कब्जा गरेको छ।'), findsOneWidget);
    });
  });

  group('AssistantMessage — normal answer', () {
    testWidgets('renders answer and disclaimer, no fake citations',
        (tester) async {
      await tester.pumpWidget(_wrap(AssistantMessage(message: _assistant())));

      expect(find.textContaining('सम्पत्ति कानून'), findsOneWidget);
      expect(find.textContaining('सामान्य कानूनी जानकारी'), findsOneWidget);
      // No citations → no sources header, no fabricated source cards.
      expect(find.textContaining('स्रोतहरू'), findsNothing);
    });

    testWidgets('shows sources header and citation card when citations exist',
        (tester) async {
      final citation = const Citation(
        document: 'मुलुकी देवानी संहिता, २०७४',
        section: '695',
        provision: 'हकवालाको निर्धारण…',
        source: 'नेपाल कानून आयोग',
        score: 0.46,
        sectionTitle: 'हकवालाको निर्धारण विदेशी कानून बमोजिम गरिने',
      );
      await tester.pumpWidget(_wrap(AssistantMessage(
        message: _assistant(citations: [citation]),
      )));
      await tester.pumpAndSettle();

      expect(find.text('स्रोतहरू (1)'), findsOneWidget);
      expect(find.textContaining('दफा 695'), findsOneWidget);
      // Source attribution is hidden until expanded.
      expect(find.byIcon(Icons.verified_outlined), findsNothing);
    });

    testWidgets('citation card expands on tap showing provision text',
        (tester) async {
      final citation = const Citation(
        document: 'मुलुकी देवानी संहिता, २०७४',
        section: '695',
        provision: 'हकवालाको निर्धारण विस्तृत पाठ…',
        source: 'नेपाल कानून आयोग',
        score: 0.46,
        sectionTitle: 'हकवालाको निर्धारण',
      );
      await tester.pumpWidget(_wrap(AssistantMessage(
        message: _assistant(citations: [citation]),
      )));
      await tester.pumpAndSettle();

      // Collapsed: provision text hidden.
      expect(find.textContaining('विस्तृत पाठ'), findsNothing);

      await tester.tap(find.textContaining('दफा 695'));
      await tester.pumpAndSettle();

      // Expanded: provision text now fully rendered (it is laid out even when
      // collapsed inside the cross-fade, so assert on the expand-only bits).
      expect(find.textContaining('नेपाल कानून आयोग'), findsOneWidget);
      expect(find.byIcon(Icons.verified_outlined), findsOneWidget);
    });
  });

  group('AssistantMessage — no-match status', () {
    testWidgets('renders the honest fallback inside a distinct card',
        (tester) async {
      await tester.pumpWidget(_wrap(AssistantMessage(
        message: ConversationMessage(
          role: 'assistant',
          content: 'प्रमाणित कानूनी प्रावधान भेटिएन।',
          status: 'no_match',
        ),
      )));

      expect(find.textContaining('प्रमाणित कानूनी प्रावधान भेटिएन'),
          findsOneWidget);
      expect(find.byIcon(Icons.search_off), findsOneWidget);
    });
  });
}

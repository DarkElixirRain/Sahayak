import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/voice/screens/voice_screen.dart';

void main() {
  Widget buildTestWidget() {
    return ProviderScope(
      child: const MaterialApp(home: VoiceScreen(sessionId: 'test-session')),
    );
  }

  group('VoiceScreen (HTML Screen 3)', () {
    testWidgets('renders title, subtitle and controls in idle state',
        (tester) async {
      await tester.pumpWidget(buildTestWidget());
      await tester.pump();

      expect(find.text('आवाजमा कुराकानी'), findsOneWidget);
      expect(find.text('भन्नुहोस्, म सुन्दैछु…'), findsOneWidget);
      // Big mic button present.
      expect(find.byIcon(Icons.mic), findsOneWidget);
      // Keyboard + close round buttons present.
      expect(find.byIcon(Icons.keyboard_alt_outlined), findsOneWidget);
      expect(find.byIcon(Icons.close), findsOneWidget);
    });

    testWidgets('shows example quote text', (tester) async {
      await tester.pumpWidget(buildTestWidget());
      await tester.pump();

      expect(find.textContaining('मेरो जग्गाको समस्या छ'), findsOneWidget);
    });
  });
}

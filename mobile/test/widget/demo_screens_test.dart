import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:sahayak_app/features/demo/presentation/demo_article_screen.dart';
import 'package:sahayak_app/features/demo/presentation/demo_cases_screen.dart';
import 'package:sahayak_app/features/demo/presentation/demo_notifications_screen.dart';
import 'package:sahayak_app/features/demo/presentation/demo_profile_screen.dart';
import 'package:sahayak_app/features/demo/presentation/demo_savedable_screen.dart';
import 'package:sahayak_app/features/demo/presentation/demo_settings_screen.dart';
import 'package:sahayak_app/main.dart';

Widget _wrap(Widget child) {
  return ProviderScope(child: MaterialApp(home: child));
}

void main() {
  group('Demo screens render fully offline', () {
    testWidgets('article screen shows seeded guidance', (tester) async {
      await tester.pumpWidget(_wrap(
        const DemoArticleScreen(articleId: 'art-bank-otp'),
      ));
      expect(find.text('कानुनी जानकारी'), findsOneWidget);
      expect(find.text('बैंक OTP सुरक्षा'), findsOneWidget);
    });

    testWidgets('saved screen lists seeded saved articles', (tester) async {
      await tester.pumpWidget(_wrap(
        const DemoSavedableScreen(searchMode: false),
      ));
      expect(find.text('बैंक OTP सुरक्षा'), findsOneWidget);
    });

    testWidgets('search screen returns results after local delay', (tester) async {
      await tester.pumpWidget(_wrap(
        const DemoSavedableScreen(searchMode: true),
      ));
      await tester.pump(const Duration(milliseconds: 700));
      // Local catalog is fully populated (no network needed).
      expect(find.byType(ListView), findsWidgets);
      expect(find.text('बैंक OTP सुरक्षा'), findsOneWidget);
    });

    testWidgets('cases screen lists informational consultations', (tester) async {
      await tester.pumpWidget(_wrap(const DemoCasesScreen()));
      expect(find.text('Online Banking Fraud'), findsOneWidget);
      expect(find.text('Guidance Provided'), findsOneWidget);
    });

    testWidgets('notifications screen shows seeded inbox', (tester) async {
      await tester.pumpWidget(_wrap(const DemoNotificationsScreen()));
      expect(find.text('सूचनाहरू'), findsOneWidget);
      expect(find.textContaining('अपडेट गरिएको छ'), findsOneWidget);
    });

    testWidgets('profile screen shows demo user', (tester) async {
      await tester.pumpWidget(_wrap(const DemoProfileScreen()));
      expect(find.text('Bishal Chaudhary'), findsOneWidget);
      expect(find.text('bishal.demo@example.com'), findsOneWidget);
      expect(find.textContaining('भर्खरको गतिविधि'), findsOneWidget);
    });

    testWidgets('settings screen shows language and notifications toggles',
        (tester) async {
      await tester.pumpWidget(_wrap(const DemoSettingsScreen()));
      expect(find.text('भाषा'), findsOneWidget);
      expect(find.text('सूचनाहरू'), findsOneWidget);
    });
  });

  group('Full app demo-mode boot (backend fully stopped)', () {
    testWidgets('onboarding → home dashboard → seeded chat', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: SahayakApp()));
      await tester.pump();

      // Demo auth auto-authenticates; tap start to enter the home dashboard.
      await tester.tap(find.text('सुरु गर्नुहोस्'));
      await tester.pumpAndSettle();

      expect(find.text('द्रुत पहुँच'), findsOneWidget);
      expect(find.text('भर्खरको'), findsOneWidget);

      // Enter the chat from the quick-action grid and confirm the OTP
      // conversation is pre-seeded locally.
      await tester.tap(find.text('अस्क सहायक'));
      await tester.pumpAndSettle();

      expect(find.textContaining('बैंक'), findsWidgets);
    });
  });
}
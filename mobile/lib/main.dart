import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/theme/app_theme.dart';
import 'features/demo/presentation/demo_article_screen.dart';
import 'features/demo/presentation/demo_cases_screen.dart';
import 'features/demo/presentation/demo_notifications_screen.dart';
import 'features/demo/presentation/demo_profile_screen.dart';
import 'features/demo/presentation/demo_savedable_screen.dart';
import 'features/demo/presentation/demo_settings_screen.dart';
import 'features/onboarding/presentation/onboarding_screen.dart';
import 'features/home/presentation/home_screen.dart';
import 'features/chat/presentation/chat_screen.dart';
import 'features/voice/presentation/voice_screen.dart';

void main() {
  runApp(
    const ProviderScope(
      child: SahayakApp(),
    ),
  );
}

class SahayakApp extends StatelessWidget {
  const SahayakApp({super.key});

  @override
  Widget build(BuildContext context) {
    final router = GoRouter(
      initialLocation: '/',
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const OnboardingScreen(),
        ),
        GoRoute(
          path: '/home',
          builder: (context, state) => const HomeScreen(),
        ),
        GoRoute(
          path: '/chat',
          builder: (context, state) {
            final extra = state.extra as Map<String, dynamic>?;
            final chatId = extra?['chatId'] as String?;
            return ChatScreen(chatId: chatId);
          },
        ),
        GoRoute(
          path: '/voice',
          builder: (context, state) => const VoiceScreen(),
        ),
        GoRoute(
          path: '/search',
          builder: (context, state) => const DemoSavedableScreen(
            searchMode: true,
          ),
        ),
        GoRoute(
          path: '/saved',
          builder: (context, state) => const DemoSavedableScreen(
            searchMode: false,
          ),
        ),
        GoRoute(
          path: '/cases',
          builder: (context, state) => const DemoCasesScreen(),
        ),
        GoRoute(
          path: '/notifications',
          builder: (context, state) => const DemoNotificationsScreen(),
        ),
        GoRoute(
          path: '/profile',
          builder: (context, state) => const DemoProfileScreen(),
        ),
        GoRoute(
          path: '/settings',
          builder: (context, state) => const DemoSettingsScreen(),
        ),
        GoRoute(
          path: '/article',
          builder: (context, state) {
            final extra = state.extra as Map<String, dynamic>?;
            final articleId = extra?['articleId'] as String? ?? '';
            return DemoArticleScreen(articleId: articleId);
          },
        ),
      ],
    );

    return MaterialApp.router(
      title: 'Sahayak',
      theme: AppTheme.lightTheme,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}

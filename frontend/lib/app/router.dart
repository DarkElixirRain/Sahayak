import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/models/auth_state.dart';
import '../features/auth/providers/auth_provider.dart';
import '../features/auth/screens/login_screen.dart';
import '../features/auth/screens/register_screen.dart';
import '../features/chat/screens/chat_screen.dart';
import '../features/conversations/screens/home_screen.dart';
import '../features/onboarding/screens/welcome_screen.dart';
import '../features/profile/screens/profile_screen.dart';
import '../features/voice/screens/voice_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/welcome',
    redirect: (context, state) {
      final uri = state.uri.toString();
      final isLoggingIn = uri == '/login';
      final isRegistering = uri == '/register';
      final isWelcome = uri == '/welcome';

      if (authState.isLoading) {
        return null; // wait for session restoration
      }

      return authState.value?.maybeWhen(
        initial: () => null,
        loading: () => null,
        unauthenticated: () {
          if (isRegistering || isWelcome || isLoggingIn) return null;
          return '/welcome';
        },
        authenticated: (_) {
          if (isLoggingIn || isRegistering || isWelcome || uri == '/') {
            return '/home';
          }
          return null;
        },
        error: (_) => '/welcome',
        orElse: () => '/welcome',
      );
    },
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) =>
            const Scaffold(body: Center(child: CircularProgressIndicator())),
      ),
      GoRoute(path: '/welcome', builder: (context, state) => const WelcomeScreen()),
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(path: '/home', builder: (context, state) => const HomeScreen()),
      GoRoute(
        path: '/profile',
        builder: (context, state) => const ProfileScreen(),
      ),
      GoRoute(
        path: '/chat/:sessionId',
        builder: (context, state) {
          final sessionId = state.pathParameters['sessionId']!;
          return ChatScreen(sessionId: sessionId);
        },
      ),
      GoRoute(
        path: '/voice/:sessionId',
        builder: (context, state) {
          final sessionId = state.pathParameters['sessionId']!;
          return VoiceScreen(sessionId: sessionId);
        },
      ),
    ],
  );
});

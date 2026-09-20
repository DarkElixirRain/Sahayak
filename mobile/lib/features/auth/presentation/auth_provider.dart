import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/demo/demo_config.dart';
import '../../../core/network/api_client.dart';
import '../data/auth_repository.dart';

final apiClientProvider = Provider((ref) => ApiClient());
final authRepositoryProvider = Provider((ref) => AuthRepository(ref.watch(apiClientProvider).dio));

final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class AuthState {
  final bool isAuthenticated;
  final bool isLoading;
  final String? error;

  AuthState({
    this.isAuthenticated = false,
    this.isLoading = true,
    this.error,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    bool? isLoading,
    String? error,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class AuthNotifier extends Notifier<AuthState> {
  late final AuthRepository _repository;

  @override
  AuthState build() {
    _repository = ref.watch(authRepositoryProvider);
    // Delay checkAuth to avoid modifying state during build
    Future.microtask(() => checkAuth());
    return AuthState();
  }

  Future<void> checkAuth() async {
    if (DemoConfig.demoMode) {
      // Deterministic local auth — no backend, no network, no stored token.
      state = state.copyWith(isAuthenticated: true, isLoading: false);
      return;
    }
    final token = await _repository.getToken();
    if (token != null) {
      state = state.copyWith(isAuthenticated: true, isLoading: false);
    } else {
      // Auto-login for local development
      try {
        await _repository.login('sahayak_dev_secret');
        state = state.copyWith(isAuthenticated: true, isLoading: false);
      } catch (e) {
        state = state.copyWith(
          isAuthenticated: false,
          isLoading: false,
          error: 'Authentication failed',
        );
      }
    }
  }

  Future<void> logout() async {
    if (DemoConfig.demoMode) {
      state = state.copyWith(isAuthenticated: false);
      return;
    }
    await _repository.clearToken();
    state = state.copyWith(isAuthenticated: false);
  }
}

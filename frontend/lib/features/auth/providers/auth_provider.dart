import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/storage/secure_storage_service.dart';
import '../data/auth_repository.dart';
import '../models/auth_state.dart';

part 'auth_provider.g.dart';

@riverpod
class AuthNotifier extends _$AuthNotifier {
  late AuthRepository _repository;
  late SecureStorageService _storage;

  @override
  FutureOr<AuthState> build() async {
    _repository = ref.watch(authRepositoryProvider);
    _storage = ref.watch(secureStorageServiceProvider);

    final token = await _storage.getToken();
    if (token == null) {
      return const AuthState.unauthenticated();
    }

    try {
      final user = await _repository.getCurrentUser();
      return AuthState.authenticated(user);
    } catch (e) {
      await _storage.deleteToken();
      return const AuthState.unauthenticated();
    }
  }

  Future<void> login(String email, String password) async {
    state = const AsyncLoading();
    try {
      final token = await _repository.login(email, password);
      await _storage.saveToken(token);
      final user = await _repository.getCurrentUser();
      state = AsyncData(AuthState.authenticated(user));
    } catch (e) {
      state = AsyncData(AuthState.error(e.toString()));
    }
  }

  Future<void> register(String email, String password, String name) async {
    state = const AsyncLoading();
    try {
      await _repository.register(email, password, name);
      final token = await _repository.login(email, password);
      await _storage.saveToken(token);
      final user = await _repository.getCurrentUser();
      state = AsyncData(AuthState.authenticated(user));
    } catch (e) {
      state = AsyncData(AuthState.error(e.toString()));
    }
  }

  Future<void> logout() async {
    await _storage.deleteToken();
    state = const AsyncData(AuthState.unauthenticated());
  }
}

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../models/user_model.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(dioClientProvider));
});

class AuthRepository {
  final Dio _dio;

  AuthRepository(this._dio);

  Future<String> login(String email, String password) async {
    final response = await _dio.post(
      '/api/auth/login',
      data: {'username': email, 'password': password},
      options: Options(contentType: 'application/x-www-form-urlencoded'),
    );
    return response.data['access_token'];
  }

  Future<void> register(String email, String password, String name) async {
    await _dio.post(
      '/api/auth/register',
      data: {'email': email, 'password': password, 'name': name},
    );
  }

  Future<User> getCurrentUser() async {
    final response = await _dio.get('/api/auth/me');
    return User.fromJson(response.data);
  }
}

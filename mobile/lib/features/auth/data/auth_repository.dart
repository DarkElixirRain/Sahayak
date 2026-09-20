import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthRepository {
  final Dio _dio;

  AuthRepository(this._dio);

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
  }

  Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
  }

  Future<String> login(String adminPassword) async {
    final formData = FormData.fromMap({
      'name': 'admin',
      'expiry_days': 30,
      'password_token': adminPassword,
      'server_mode': false,
    });

    final response = await _dio.post(
      '/local/generate_uri',
      data: formData,
      options: Options(
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      ),
    );

    if (response.statusCode == 200) {
      final uri = response.data['uri'] as String;
      // uri format: morphik://name:token@host:port
      final tokenPart = uri.split('://')[1].split('@')[0];
      final token = tokenPart.split(':')[1];
      await saveToken(token);
      return token;
    } else {
      throw Exception('Authentication failed');
    }
  }
}

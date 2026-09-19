import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants/app_config.dart';
import '../errors/app_exceptions.dart';
import '../storage/secure_storage_service.dart';

final dioClientProvider = Provider<Dio>((ref) {
  final storage = ref.watch(secureStorageServiceProvider);

  final dio = Dio(
    BaseOptions(
      baseUrl: AppConfig.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 45), // Voice may take longer
      headers: {
        HttpHeaders.contentTypeHeader: 'application/json',
        HttpHeaders.acceptHeader: 'application/json',
      },
    ),
  );

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await storage.getToken();
        if (token != null) {
          options.headers[HttpHeaders.authorizationHeader] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        return handler.next(_handleDioError(e));
      },
    ),
  );

  return dio;
});

DioException _handleDioError(DioException error) {
  AppException appException;

  if (error.type == DioExceptionType.connectionTimeout ||
      error.type == DioExceptionType.receiveTimeout ||
      error.type == DioExceptionType.sendTimeout) {
    appException = NetworkException(
      'Connection timed out. Please check your internet connection.',
    );
  } else if (error.type == DioExceptionType.connectionError) {
    appException = NetworkException(
      'Could not connect to Sahayak. Please check your internet connection.',
    );
  } else if (error.response != null) {
    final statusCode = error.response!.statusCode;
    final data = error.response!.data;

    String message = 'An unexpected error occurred.';
    if (data is Map<String, dynamic>) {
      if (data['error'] != null && data['error']['message'] != null) {
        message = data['error']['message'].toString();
      } else if (data['detail'] != null) {
        if (data['detail'] is String) {
          message = data['detail'].toString();
        } else if (data['detail'] is List) {
          message = 'Validation Error. Please check your input.';
        }
      }
    }

    if (statusCode == 400) {
      appException = ValidationException(message);
    } else if (statusCode == 401) {
      appException = UnauthorizedException(message);
    } else if (statusCode == 403) {
      appException = UnauthorizedException('Forbidden: $message');
    } else if (statusCode == 404) {
      appException = ServerException('Not found.');
    } else if (statusCode == 422) {
      appException = ValidationException(message);
    } else if (statusCode != null && statusCode >= 500) {
      appException = ServerException(
        'Sahayak is currently unavailable (Server Error). Please try again later.',
      );
    } else {
      appException = UnknownException(message);
    }
  } else {
    appException = UnknownException(error.message ?? 'Unknown error occurred.');
  }

  return DioException(
    requestOptions: error.requestOptions,
    response: error.response,
    type: error.type,
    error: appException,
  );
}

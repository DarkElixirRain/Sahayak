class AppException implements Exception {
  final String message;
  final String? code;

  AppException(this.message, {this.code});

  @override
  String toString() => message;
}

class NetworkException extends AppException {
  NetworkException(super.message);
}

class UnauthorizedException extends AppException {
  UnauthorizedException(super.message);
}

class ValidationException extends AppException {
  final Map<String, dynamic>? errors;
  ValidationException(super.message, {this.errors});
}

class ServerException extends AppException {
  ServerException(super.message);
}

class UnknownException extends AppException {
  UnknownException([super.message = 'An unexpected error occurred.']);
}

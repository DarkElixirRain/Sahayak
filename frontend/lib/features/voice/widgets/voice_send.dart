import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/app_limits.dart';
import '../../../core/errors/app_exceptions.dart';
import '../../chat/data/chat_repository.dart';
import '../../chat/providers/chat_provider.dart';

/// Sends a recorded voice file through the real chat repository and maps
/// failures to friendly Nepali messages.
///
/// Takes [WidgetRef] directly (no BuildContext) so callers can safely use it
/// across async gaps.
///
/// The chat provider preloads the conversation after a successful send so the
/// chat screen shows the transcript + reply immediately.
///
/// Returns a user-friendly error string, or null when the upload succeeded.
Future<String?> sendVoiceFileWithRef(
  WidgetRef ref,
  String sessionId,
  String filePath,
) async {
  final file = File(filePath);
  final maxBytes = AppLimits.maxAudioSizeMb * 1024 * 1024;
  if (await file.length() > maxBytes) {
    return 'अडियो फाइल ${AppLimits.maxAudioSizeMb} MB भन्दा सानो हुनुपर्छ।';
  }

  final repository = ref.read(chatRepositoryProvider);
  try {
    final response = await repository.sendVoiceMessage(sessionId, filePath);
    // Preload the conversation so the chat screen opens with the full turn.
    await ref.read(chatProvider(sessionId).notifier).adoptVoiceResponse(response);
    return null;
  } on ValidationException catch (e) {
    return e.message;
  } on NetworkException catch (e) {
    return e.message;
  } on ServerException catch (e) {
    return e.message;
  } on UnauthorizedException {
    return 'सेसन समाप्त भयो। फेरि लगइन गर्नुहोस्।';
  } catch (_) {
    return 'भ्वाइस मेसेज पठाउन सकिएन। फेरि प्रयास गर्नुहोस्।';
  }
}

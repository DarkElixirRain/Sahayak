import 'package:freezed_annotation/freezed_annotation.dart';

part 'chat_models.freezed.dart';
part 'chat_models.g.dart';

@freezed
sealed class ConversationMessage with _$ConversationMessage {
  const factory ConversationMessage({
    required String role,
    @Default('') String content,
    @JsonKey(name: 'created_at') String? createdAt,
    String? audio,
    @Default(<Citation>[]) List<Citation> citations,
    @Default(false) bool grounded,
    String? status,
    String? disclaimer,
  }) = _ConversationMessage;

  factory ConversationMessage.fromJson(Map<String, dynamic> json) =>
      _$ConversationMessageFromJson(json);
}

@freezed
sealed class Citation with _$Citation {
  const factory Citation({
    required String document,
    required String section,
    required String provision,
    required String source,
    required double score,
    @JsonKey(name: 'source_url') String? sourceUrl,
  }) = _Citation;

  factory Citation.fromJson(Map<String, dynamic> json) =>
      _$CitationFromJson(json);
}

@freezed
sealed class FollowUpQuestion with _$FollowUpQuestion {
  const factory FollowUpQuestion({required String question, String? reason}) =
      _FollowUpQuestion;

  factory FollowUpQuestion.fromJson(Map<String, dynamic> json) =>
      _$FollowUpQuestionFromJson(json);
}

@freezed
sealed class ConversationResponse with _$ConversationResponse {
  const factory ConversationResponse({
    required String answer,
    @Default('low') String confidence,
    @Default('') String disclaimer,
    @Default(<Citation>[]) List<Citation> citations,
    @JsonKey(name: 'follow_up_questions')
    @Default(<FollowUpQuestion>[])
    List<FollowUpQuestion> followUpQuestions,
    @JsonKey(name: 'needs_clarification')
    @Default(false)
    bool needsClarification,
    @Default('answered') String status,
    @Default(false) bool grounded,
    @Default('none') String generation,
    @JsonKey(name: 'llm_provider') String? llmProvider,
    @JsonKey(name: 'llm_model') String? llmModel,
    @JsonKey(name: 'llm_error') String? llmError,
    @JsonKey(name: 'retrieval_status') String? retrievalStatus,
    @JsonKey(name: 'retrieval_total_found')
    @Default(0)
    int retrievalTotalFound,
    @JsonKey(name: 'unverified_match_count')
    @Default(0)
    int unverifiedMatchCount,
    @JsonKey(name: 'search_terms') @Default(<String>[]) List<String> searchTerms,
    String? audio,
  }) = _ConversationResponse;

  factory ConversationResponse.fromJson(Map<String, dynamic> json) =>
      _$ConversationResponseFromJson(json);
}

@freezed
sealed class ConversationStatus with _$ConversationStatus {
  const factory ConversationStatus({
    @JsonKey(name: 'session_id') required String sessionId,
    required String status,
    @Default('nepali') String language,
    @JsonKey(name: 'message_count') @Default(0) int messageCount,
    @JsonKey(name: 'started_at') String? startedAt,
    @Default(<ConversationMessage>[]) List<ConversationMessage> messages,
  }) = _ConversationStatus;

  factory ConversationStatus.fromJson(Map<String, dynamic> json) =>
      _$ConversationStatusFromJson(json);
}

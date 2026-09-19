// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_ConversationMessage _$ConversationMessageFromJson(Map<String, dynamic> json) =>
    _ConversationMessage(
      role: json['role'] as String,
      content: json['content'] as String? ?? '',
      createdAt: json['created_at'] as String?,
      audio: json['audio'] as String?,
      citations:
          (json['citations'] as List<dynamic>?)
              ?.map((e) => Citation.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const <Citation>[],
      grounded: json['grounded'] as bool? ?? false,
      status: json['status'] as String?,
      disclaimer: json['disclaimer'] as String?,
    );

Map<String, dynamic> _$ConversationMessageToJson(
  _ConversationMessage instance,
) => <String, dynamic>{
  'role': instance.role,
  'content': instance.content,
  'created_at': instance.createdAt,
  'audio': instance.audio,
  'citations': instance.citations,
  'grounded': instance.grounded,
  'status': instance.status,
  'disclaimer': instance.disclaimer,
};

_Citation _$CitationFromJson(Map<String, dynamic> json) => _Citation(
  document: json['document'] as String,
  section: json['section'] as String,
  provision: json['provision'] as String,
  source: json['source'] as String,
  score: (json['score'] as num).toDouble(),
  sourceUrl: json['source_url'] as String?,
);

Map<String, dynamic> _$CitationToJson(_Citation instance) => <String, dynamic>{
  'document': instance.document,
  'section': instance.section,
  'provision': instance.provision,
  'source': instance.source,
  'score': instance.score,
  'source_url': instance.sourceUrl,
};

_FollowUpQuestion _$FollowUpQuestionFromJson(Map<String, dynamic> json) =>
    _FollowUpQuestion(
      question: json['question'] as String,
      reason: json['reason'] as String?,
    );

Map<String, dynamic> _$FollowUpQuestionToJson(_FollowUpQuestion instance) =>
    <String, dynamic>{'question': instance.question, 'reason': instance.reason};

_ConversationResponse _$ConversationResponseFromJson(
  Map<String, dynamic> json,
) => _ConversationResponse(
  answer: json['answer'] as String,
  confidence: json['confidence'] as String? ?? 'low',
  disclaimer: json['disclaimer'] as String? ?? '',
  citations:
      (json['citations'] as List<dynamic>?)
          ?.map((e) => Citation.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const <Citation>[],
  followUpQuestions:
      (json['follow_up_questions'] as List<dynamic>?)
          ?.map((e) => FollowUpQuestion.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const <FollowUpQuestion>[],
  needsClarification: json['needs_clarification'] as bool? ?? false,
  status: json['status'] as String? ?? 'answered',
  grounded: json['grounded'] as bool? ?? false,
  generation: json['generation'] as String? ?? 'none',
  llmProvider: json['llm_provider'] as String?,
  llmModel: json['llm_model'] as String?,
  llmError: json['llm_error'] as String?,
  retrievalStatus: json['retrieval_status'] as String?,
  retrievalTotalFound: (json['retrieval_total_found'] as num?)?.toInt() ?? 0,
  unverifiedMatchCount: (json['unverified_match_count'] as num?)?.toInt() ?? 0,
  searchTerms:
      (json['search_terms'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const <String>[],
  audio: json['audio'] as String?,
);

Map<String, dynamic> _$ConversationResponseToJson(
  _ConversationResponse instance,
) => <String, dynamic>{
  'answer': instance.answer,
  'confidence': instance.confidence,
  'disclaimer': instance.disclaimer,
  'citations': instance.citations,
  'follow_up_questions': instance.followUpQuestions,
  'needs_clarification': instance.needsClarification,
  'status': instance.status,
  'grounded': instance.grounded,
  'generation': instance.generation,
  'llm_provider': instance.llmProvider,
  'llm_model': instance.llmModel,
  'llm_error': instance.llmError,
  'retrieval_status': instance.retrievalStatus,
  'retrieval_total_found': instance.retrievalTotalFound,
  'unverified_match_count': instance.unverifiedMatchCount,
  'search_terms': instance.searchTerms,
  'audio': instance.audio,
};

_ConversationStatus _$ConversationStatusFromJson(Map<String, dynamic> json) =>
    _ConversationStatus(
      sessionId: json['session_id'] as String,
      status: json['status'] as String,
      language: json['language'] as String? ?? 'nepali',
      messageCount: (json['message_count'] as num?)?.toInt() ?? 0,
      startedAt: json['started_at'] as String?,
      messages:
          (json['messages'] as List<dynamic>?)
              ?.map(
                (e) => ConversationMessage.fromJson(e as Map<String, dynamic>),
              )
              .toList() ??
          const <ConversationMessage>[],
    );

Map<String, dynamic> _$ConversationStatusToJson(_ConversationStatus instance) =>
    <String, dynamic>{
      'session_id': instance.sessionId,
      'status': instance.status,
      'language': instance.language,
      'message_count': instance.messageCount,
      'started_at': instance.startedAt,
      'messages': instance.messages,
    };

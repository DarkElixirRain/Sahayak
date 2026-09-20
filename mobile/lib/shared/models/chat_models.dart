import 'dart:convert';

class Citation {
  final String documentId;
  final int chunkNumber;
  final double score;

  Citation({
    required this.documentId,
    required this.chunkNumber,
    required this.score,
  });

  factory Citation.fromJson(Map<String, dynamic> json) {
    return Citation(
      documentId: json['document_id'] ?? '',
      chunkNumber: json['chunk_number'] ?? 0,
      score: (json['score'] ?? 0.0).toDouble(),
    );
  }
}

class ApplicableLaw {
  final String actName;
  final String section;
  final String explanation;
  final String sourceId;

  ApplicableLaw({
    required this.actName,
    required this.section,
    required this.explanation,
    required this.sourceId,
  });

  factory ApplicableLaw.fromJson(Map<String, dynamic> json) {
    return ApplicableLaw(
      actName: json['act_name']?.toString() ?? '',
      section: json['section']?.toString() ?? '',
      explanation: json['explanation']?.toString() ?? '',
      sourceId: json['source_id']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'act_name': actName,
        'section': section,
        'explanation': explanation,
        'source_id': sourceId,
      };
}

class StructuredLegalAnswer {
  final String responseType;
  final String message;
  final String summary;
  final String issue;
  final List<ApplicableLaw> applicableLaws;
  final String explanation;
  final List<String> nextSteps;
  final List<String> clarifyingQuestions;

  StructuredLegalAnswer({
    required this.responseType,
    required this.message,
    required this.summary,
    required this.issue,
    required this.applicableLaws,
    required this.explanation,
    required this.nextSteps,
    required this.clarifyingQuestions,
  });

  factory StructuredLegalAnswer.fromJson(Map<String, dynamic> json) {
    return StructuredLegalAnswer(
      responseType: json['response_type']?.toString() ?? 'legal_answer',
      message: json['message']?.toString() ?? '',
      summary: json['summary']?.toString() ?? '',
      issue: json['issue']?.toString() ?? '',
      applicableLaws: (json['applicable_laws'] as List<dynamic>?)
              ?.map((e) {
                if (e is String) {
                  return ApplicableLaw(actName: e, section: '', explanation: '', sourceId: '');
                } else if (e is Map<String, dynamic>) {
                  return ApplicableLaw.fromJson(e);
                }
                return ApplicableLaw(actName: 'Unknown', section: '', explanation: '', sourceId: '');
              })
              .toList() ??
          [],
      explanation: json['explanation']?.toString() ?? '',
      nextSteps: (json['next_steps'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      clarifyingQuestions: (json['clarifying_questions'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() => {
        'response_type': responseType,
        'message': message,
        'summary': summary,
        'issue': issue,
        'applicable_laws': applicableLaws.map((e) => e.toJson()).toList(),
        'explanation': explanation,
        'next_steps': nextSteps,
        'clarifying_questions': clarifyingQuestions,
      };
}

class QueryResponse {
  final String text;
  final StructuredLegalAnswer? structuredAnswer;
  final List<Citation> sources;
  final String finishReason;
  final String? audioUrl;

  QueryResponse({
    required this.text,
    this.structuredAnswer,
    required this.sources,
    required this.finishReason,
    this.audioUrl,
  });

  factory QueryResponse.fromJson(Map<String, dynamic> json) {
    final completionData = json['completion'] ?? json['text'];
    String textVal = '';
    StructuredLegalAnswer? structured;

    if (completionData is Map<String, dynamic>) {
      try {
        structured = StructuredLegalAnswer.fromJson(completionData);
      } catch (e) {
        // Fallback if parsing fails
      }
      textVal = jsonEncode(completionData);
    } else if (completionData is String) {
      textVal = completionData;
      // Try to parse if it's a JSON string
      try {
        final decoded = jsonDecode(completionData);
        if (decoded is Map<String, dynamic>) {
          structured = StructuredLegalAnswer.fromJson(decoded);
        }
      } catch (_) {}
    }
    
    var sourcesList = <Citation>[];
    if (json['sources'] != null && json['sources'] is List) {
      sourcesList = (json['sources'] as List)
          .map((e) => Citation.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    
    return QueryResponse(
      text: textVal,
      structuredAnswer: structured,
      sources: sourcesList,
      finishReason: json['finish_reason'] ?? '',
      audioUrl: json['audio_url']?.toString(),
    );
  }
}

class ChatMessage {
  final String id;
  final String content;
  final bool isUser;
  final DateTime timestamp;
  final List<Citation> sources;
  StructuredLegalAnswer? structuredAnswer;
  final String? audioUrl;

  ChatMessage({
    required this.id,
    required this.content,
    required this.isUser,
    required this.timestamp,
    this.sources = const [],
    this.structuredAnswer,
    this.audioUrl,
  }) {
    if (!isUser && structuredAnswer == null) {
      // Try to parse content as JSON just in case it was stored as JSON string
      try {
        final decoded = jsonDecode(content);
        if (decoded is Map<String, dynamic> && decoded.containsKey('summary')) {
          structuredAnswer = StructuredLegalAnswer.fromJson(decoded);
        }
      } catch (_) {}
    }
  }
}

import '../../shared/models/chat_models.dart';

/// Converts a [StructuredLegalAnswer] into natural spoken text suitable for
/// TTS playback.
///
/// Rules:
/// - NEVER include citation metadata (document IDs, chunk numbers, scores)
/// - NEVER include raw JSON or UI labels
/// - NEVER include empty sections
/// - For casual → speak [message]
/// - For legal_clarification → speak [message] + clarifying questions
/// - For legal_answer → speak summary → issue → law names → explanation → next steps
String answerToSpeech(StructuredLegalAnswer answer) {
  final type = answer.responseType.toLowerCase();

  switch (type) {
    case 'casual':
      return _clean(answer.message);

    case 'legal_clarification':
      final parts = <String>[];

      if (answer.message.isNotEmpty) {
        parts.add(_clean(answer.message));
      }

      if (answer.clarifyingQuestions.isNotEmpty) {
        // Speak only the first 1-2 questions; reading all of them sounds robotic.
        final questions = answer.clarifyingQuestions.take(2).toList();
        if (questions.length == 1) {
          parts.add(questions.first);
        } else {
          parts.add(questions.join(' अथवा '));
        }
      }

      return parts.join(' ');

    case 'legal_answer':
      return _buildLegalAnswerSpeech(answer);

    default:
      // Unknown type — just speak the message field.
      return _clean(answer.message.isNotEmpty ? answer.message : answer.summary);
  }
}

String _buildLegalAnswerSpeech(StructuredLegalAnswer answer) {
  final parts = <String>[];

  // 1. Summary — most important, speak first.
  if (answer.summary.isNotEmpty) {
    parts.add(_clean(answer.summary));
  }

  // 2. Legal issue context.
  if (answer.issue.isNotEmpty) {
    parts.add('यस विषयमा ${_clean(answer.issue)} सम्बन्धी कानुनी व्यवस्था लागू हुन्छ।');
  }

  // 3. Applicable laws — speak act names + section only; skip source_id.
  if (answer.applicableLaws.isNotEmpty) {
    final lawNames = answer.applicableLaws
        .where((l) => l.actName.isNotEmpty)
        .map((l) {
          final name = _clean(l.actName);
          final section = l.section.isNotEmpty ? ', ${_clean(l.section)}' : '';
          return '$name$section';
        })
        .take(3) // cap at 3 to keep TTS digestible
        .join('; ');
    if (lawNames.isNotEmpty) {
      parts.add('लागू हुने कानुनमा $lawNames समावेश छ।');
    }
  }

  // 4. Explanation.
  if (answer.explanation.isNotEmpty) {
    parts.add(_clean(answer.explanation));
  }

  // 5. Next steps — read as a list with ordinals.
  if (answer.nextSteps.isNotEmpty) {
    parts.add('अब तपाईंले गर्नुपर्ने कदमहरू:');
    final steps = answer.nextSteps
        .take(4) // cap at 4 steps
        .toList();
    for (int i = 0; i < steps.length; i++) {
      parts.add('${i + 1}. ${_clean(steps[i])}');
    }
  }

  // 6. Fallback if nothing was added.
  if (parts.isEmpty && answer.message.isNotEmpty) {
    parts.add(_clean(answer.message));
  }

  return parts.join(' ');
}

/// Remove markdown characters and excessive whitespace from [text].
String _clean(String text) {
  return text
      .replaceAll(RegExp(r'\*+'), '')       // bold/italic asterisks
      .replaceAll(RegExp(r'#+\s*'), '')      // heading hashes
      .replaceAll(RegExp(r'`+'), '')         // code ticks
      .replaceAll(RegExp(r'\[([^\]]+)\]\([^)]+\)'), r'$1') // markdown links → text
      .replaceAll(RegExp(r'\s+'), ' ')       // collapse whitespace
      .trim();
}

/// Detect dominant language of [text] to pick the right TTS locale.
/// Returns "ne-NP" if the text contains Devanagari, "en-US" otherwise.
String detectLanguage(String text) {
  // Devanagari Unicode block: U+0900–U+097F
  final devanagariPattern = RegExp(r'[\u0900-\u097F]');
  if (devanagariPattern.hasMatch(text)) {
    return 'ne-NP';
  }
  return 'en-US';
}

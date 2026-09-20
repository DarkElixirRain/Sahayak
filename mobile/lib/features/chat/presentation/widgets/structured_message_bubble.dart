import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../shared/models/chat_models.dart';
import 'citations_section.dart';

class StructuredMessageBubble extends StatelessWidget {
  final ChatMessage message;
  final Function(String) onQuestionTap;

  const StructuredMessageBubble({
    super.key,
    required this.message,
    required this.onQuestionTap,
  });

  @override
  Widget build(BuildContext context) {
    final answer = message.structuredAnswer;
    
    // Fallback if not structured (should be handled in chat_screen, but just in case)
    if (answer == null) {
      return Align(
        alignment: Alignment.centerLeft,
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 6),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.cardBg,
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(20),
              topRight: Radius.circular(20),
              bottomLeft: Radius.circular(4),
              bottomRight: Radius.circular(20),
            ),
            border: Border.all(color: AppColors.cardBorder),
            boxShadow: [
              BoxShadow(
                color: AppColors.ink.withValues(alpha: 0.05),
                blurRadius: 10,
                offset: const Offset(0, 4),
              )
            ],
          ),
          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.85),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                message.content,
                style: const TextStyle(
                  color: AppColors.inkSoft,
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                ),
              ),
              if (message.sources.isNotEmpty)
                CitationsSection(sources: message.sources),
            ],
          ),
        ),
      );
    }

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        decoration: BoxDecoration(
          color: AppColors.cardBg,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
            bottomLeft: Radius.circular(4),
            bottomRight: Radius.circular(20),
          ),
          border: Border.all(color: AppColors.cardBorder),
          boxShadow: [
            BoxShadow(
              color: AppColors.ink.withValues(alpha: 0.05),
              blurRadius: 10,
              offset: const Offset(0, 4),
            )
          ],
        ),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.85),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (answer.issue.isNotEmpty) _buildIssueCard(answer.issue),
            if (answer.summary.isNotEmpty) ...[
              const SizedBox(height: 12),
              _buildSummaryText(answer.summary),
            ],
            if (answer.applicableLaws.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildApplicableLawSection(answer.applicableLaws),
            ] else ...[
              const SizedBox(height: 16),
              _buildNoLawFound(),
            ],
            if (answer.explanation.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildExplanationCard(answer.explanation),
            ],
            if (answer.nextSteps.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildNextStepsCard(answer.nextSteps),
            ],
            if (answer.clarifyingQuestions.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildClarifyingQuestions(answer.clarifyingQuestions),
            ],
            if (message.sources.isNotEmpty) ...[
              const SizedBox(height: 16),
              CitationsSection(sources: message.sources),
            ],
            const SizedBox(height: 16),
            _buildDisclaimer(),
          ],
        ),
      ),
    );
  }

  Widget _buildIssueCard(String issue) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.purple2.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.purple2.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('⚖️ ', style: TextStyle(fontSize: 14)),
          Flexible(
            child: Text(
              'कानुनी विषय: $issue',
              style: const TextStyle(
                color: AppColors.purple1,
                fontWeight: FontWeight.w600,
                fontSize: 13,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryText(String summary) {
    return Text(
      summary,
      style: const TextStyle(
        color: AppColors.inkSoft,
        fontSize: 15,
        height: 1.5,
        fontWeight: FontWeight.w500,
      ),
    );
  }

  Widget _buildNoLawFound() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.orange.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.orange.withValues(alpha: 0.3)),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline, color: Colors.orange, size: 20),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              'उपलब्ध स्रोतबाट ठ्याक्कै दफा पुष्टि गर्न थप विवरण आवश्यक छ।',
              style: TextStyle(
                color: Colors.brown,
                fontSize: 14,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildApplicableLawSection(List<ApplicableLaw> laws) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          children: [
            Text('📖 ', style: TextStyle(fontSize: 16)),
            Text(
              'लागू हुने कानुनी व्यवस्था',
              style: TextStyle(
                color: AppColors.ink,
                fontWeight: FontWeight.bold,
                fontSize: 15,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ...laws.map((law) => Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.cardBorder),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    law.actName,
                    style: const TextStyle(
                      color: AppColors.purple1,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                  if (law.section.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        law.section,
                        style: const TextStyle(
                          color: AppColors.inkSoft,
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  if (law.explanation.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(
                        law.explanation,
                        style: const TextStyle(
                          color: AppColors.muted,
                          fontSize: 13,
                          height: 1.4,
                        ),
                      ),
                    ),
                ],
              ),
            )),
      ],
    );
  }

  Widget _buildExplanationCard(String explanation) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.cardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Text('🔎 ', style: TextStyle(fontSize: 16)),
              Text(
                'किन यो लागू हुन्छ?',
                style: TextStyle(
                  color: AppColors.ink,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            explanation,
            style: const TextStyle(
              color: AppColors.inkSoft,
              fontSize: 14,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNextStepsCard(List<String> nextSteps) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.cardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Text('💡 ', style: TextStyle(fontSize: 16)),
              Text(
                'अब के गर्ने?',
                style: TextStyle(
                  color: AppColors.ink,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ...nextSteps.asMap().entries.map((entry) {
            int idx = entry.key;
            String step = entry.value;
            return Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 20,
                    height: 20,
                    alignment: Alignment.center,
                    decoration: const BoxDecoration(
                      color: AppColors.purple1,
                      shape: BoxShape.circle,
                    ),
                    child: Text(
                      '${idx + 1}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      step,
                      style: const TextStyle(
                        color: AppColors.inkSoft,
                        fontSize: 14,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildClarifyingQuestions(List<String> questions) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'थप स्पष्ट गर्न:',
          style: TextStyle(
            color: AppColors.ink,
            fontWeight: FontWeight.bold,
            fontSize: 14,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: questions.map((q) => ActionChip(
                label: Text(q),
                labelStyle: const TextStyle(
                  color: AppColors.purple1,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
                backgroundColor: AppColors.purple2.withValues(alpha: 0.1),
                side: BorderSide(color: AppColors.purple2.withValues(alpha: 0.3)),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                onPressed: () => onQuestionTap(q),
              )).toList(),
        ),
      ],
    );
  }

  Widget _buildDisclaimer() {
    return const Text(
      'यो सामान्य कानुनी जानकारी हो। वास्तविक कानुनी प्रक्रियाका लागि योग्य कानुनी सल्लाह लिनुहोस्।',
      style: TextStyle(
        color: AppColors.muted,
        fontSize: 11,
        fontStyle: FontStyle.italic,
      ),
      textAlign: TextAlign.center,
    );
  }
}

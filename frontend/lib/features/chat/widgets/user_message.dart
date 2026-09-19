import 'package:flutter/material.dart';

import '../../../app/theme/sahayak_theme.dart';
import '../models/chat_models.dart';

/// User bubble — soft glass bubble with the tail on the right
/// (mirrors `.s1-bubble` corner language: 20/20/20/4 flipped).
class UserMessage extends StatelessWidget {
  final ConversationMessage message;

  const UserMessage({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Flexible(
            child: Container(
              constraints: const BoxConstraints(maxWidth: 320),
              padding:
                  const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                gradient: SahayakColors.filledBtnGradient,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(18),
                  topRight: Radius.circular(18),
                  bottomLeft: Radius.circular(18),
                  bottomRight: Radius.circular(4),
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF6a58e0).withValues(alpha: .30),
                    blurRadius: 14,
                    offset: const Offset(0, 6),
                    spreadRadius: -6,
                  ),
                ],
              ),
              child: SelectableText(
                message.content,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14.5,
                  height: 1.4,
                ),
              ),
            ),
          ),
          if (!isDark) const SizedBox(width: 2),
        ],
      ),
    );
  }
}

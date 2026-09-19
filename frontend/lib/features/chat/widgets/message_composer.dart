import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';

import '../../../app/theme/sahayak_theme.dart';
import '../../../core/constants/app_limits.dart';
import '../../voice/widgets/voice_record_button.dart';

/// `.composer` — frosted pill with mic + input + gradient send button.
///
/// * Respects the backend's 2000-character limit with a visible counter and a
///   friendly Nepali warning when exceeded (never silently truncates).
/// * Send is disabled while a request is in flight (duplicate-send protection)
///   and when the input is empty.
class MessageComposer extends HookWidget {
  final TextEditingController controller;
  final bool isSending;
  final ValueChanged<String> onSendText;
  final ValueChanged<String> onSendVoice;

  const MessageComposer({
    super.key,
    required this.controller,
    required this.isSending,
    required this.onSendText,
    required this.onSendVoice,
  });

  @override
  Widget build(BuildContext context) {
    final hasText = useState(false);
    final length = useState(0);

    useEffect(() {
      void listener() {
        final value = controller.text.trim().isNotEmpty;
        if (value != hasText.value) hasText.value = value;
        if (controller.text.length != length.value) {
          length.value = controller.text.length;
        }
      }

      controller.addListener(listener);
      return () => controller.removeListener(listener);
    }, [controller]);

    final overLimit = length.value > AppLimits.maxMessageLength;
    final canSend = hasText.value && !isSending && !overLimit;
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 4, 12, 10),
      child: Column(
        children: [
          if (overLimit)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                children: [
                  Icon(Icons.error_outline,
                      size: 14, color: theme.colorScheme.error),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'सन्देश ${AppLimits.maxMessageLength} अक्षरभन्दा लामो हुन सक्दैन '
                      '(हाल ${length.value})। कृपया छोटो गर्नुहोस्।',
                      style: TextStyle(
                          fontSize: 12, color: theme.colorScheme.error),
                    ),
                  ),
                ],
              ),
            )
          else if (length.value > AppLimits.maxMessageLength - 200)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text(
                '${AppLimits.maxMessageLength - length.value} अक्षर बाँकी',
                style: TextStyle(
                    fontSize: 11, color: theme.colorScheme.onSurfaceVariant),
              ),
            ),
          Container(
            padding: const EdgeInsets.fromLTRB(6, 6, 6, 6),
            decoration: BoxDecoration(
              color: isDark
                  ? Colors.white.withValues(alpha: .08)
                  : const Color(0xc7ffffff),
              borderRadius: BorderRadius.circular(28),
              border: Border.all(color: Colors.white.withValues(alpha: .6)),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF46366e).withValues(alpha: .14),
                  blurRadius: 24,
                  offset: const Offset(0, 10),
                  spreadRadius: -14,
                ),
              ],
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                VoiceRecordButton(
                  enabled: !isSending,
                  onRecordingComplete: onSendVoice,
                ),
                Expanded(
                  child: TextField(
                    controller: controller,
                    enabled: !isSending,
                    minLines: 1,
                    maxLines: 5,
                    keyboardType: TextInputType.multiline,
                    textInputAction: TextInputAction.newline,
                    style: const TextStyle(fontSize: 14.5, height: 1.4),
                    decoration: InputDecoration(
                      hintText: 'आफ्नो कानुनी प्रश्न लेख्नुहोस्…',
                      counterText: '',
                      filled: false,
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 12),
                      hintStyle: TextStyle(
                          fontSize: 14,
                          color: theme.colorScheme.onSurfaceVariant
                              .withValues(alpha: .7)),
                    ),
                  ),
                ),
                const SizedBox(width: 4),
                // Send button — gradient circle (duplicate-send protection).
                Semantics(
                  button: true,
                  label: 'Send message',
                  child: GestureDetector(
                    onTap: canSend ? () => onSendText(controller.text) : null,
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: canSend
                            ? SahayakColors.filledBtnGradient
                            : null,
                        color: canSend
                            ? null
                            : theme.colorScheme.onSurface
                                .withValues(alpha: .08),
                      ),
                      child: Center(
                        child: isSending
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2, color: Colors.white),
                              )
                            : Icon(Icons.arrow_upward,
                                size: 20,
                                color: canSend
                                    ? Colors.white
                                    : theme.colorScheme.onSurfaceVariant
                                        .withValues(alpha: .5)),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../chat/presentation/chat_provider.dart';
import '../domain/voice_notifier.dart';

/// Full voice conversation screen.
///
/// Design matches the existing Sahayak visual language (gradients, colors,
/// typography).  The screen keeps the user in a continuous listen→process
/// →speak→listen loop until they explicitly stop.
class VoiceScreen extends ConsumerStatefulWidget {
  const VoiceScreen({super.key});

  @override
  ConsumerState<VoiceScreen> createState() => _VoiceScreenState();
}

class _VoiceScreenState extends ConsumerState<VoiceScreen>
    with TickerProviderStateMixin {
  // Pulse animation for the mic orb while listening.
  late final AnimationController _pulseController;
  late final Animation<double> _pulseAnim;

  // Language selection: true = Nepali, false = English.
  bool _nepali = true;

  // Captured in initState so we never touch `ref` during dispose(), which
  // Riverpod forbids ("Using ref when a widget is about to or has been
  // unmounted is unsafe"). The notifier stays alive for the provider's
  // lifetime, so it is safe to call from dispose().
  late final VoiceNotifier _voiceNotifier;

  @override
  void initState() {
    super.initState();

    _voiceNotifier = ref.read(voiceProvider.notifier);

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);

    _pulseAnim = Tween<double>(begin: 0.92, end: 1.08).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    // Start the voice session automatically when screen opens.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _voiceNotifier.startSession();
    });
  }

  @override
  void dispose() {
    _pulseController.dispose();
    // End the session when the screen is removed from the tree.
    _voiceNotifier.endSession();
    super.dispose();
  }

  // ── Actions ──────────────────────────────────────────────────────────────

  void _handleOrbTap(VoiceConversationState status) {
    final notifier = ref.read(voiceProvider.notifier);
    switch (status) {
      case VoiceConversationState.idle:
      case VoiceConversationState.ended:
      case VoiceConversationState.error:
        notifier.startSession();
      case VoiceConversationState.listening:
        // Stop current recognition without ending the whole session
        // (user wants to cancel this utterance).
        notifier.endSession();
      case VoiceConversationState.speaking:
        // Interrupt TTS → resume listening.
        notifier.interrupt();
      default:
        break; // Don't interfere during processing / responding.
    }
  }

  void _toggleLanguage() {
    setState(() => _nepali = !_nepali);
    final locale = _nepali ? 'ne-NP' : 'en-US';
    ref.read(voiceProvider.notifier).setLanguage(locale);
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final voiceState = ref.watch(voiceProvider);
    final chatState = ref.watch(chatProvider);

    // Drive pulse animation based on voice state.
    if (voiceState.status == VoiceConversationState.listening) {
      if (!_pulseController.isAnimating) _pulseController.repeat(reverse: true);
    } else {
      _pulseController.stop();
      _pulseController.value = 0;
    }

    return PopScope(
      onPopInvokedWithResult: (didPop, _) {
        if (didPop) ref.read(voiceProvider.notifier).endSession();
      },
      child: Scaffold(
        body: Container(
          width: double.infinity,
          height: double.infinity,
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Color(0xFFEFEAE4), Color(0xFFE7E3EF), Color(0xFFE3E7F2)],
            ),
          ),
          child: SafeArea(
            child: Column(
              children: [
                _buildTopBar(context, voiceState),
                Expanded(child: _buildOrbArea(voiceState)),
                _buildTranscriptArea(voiceState),
                _buildLastAiMessage(chatState),
                _buildBottomBar(voiceState),
                const SizedBox(height: 16),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ── Top bar ──────────────────────────────────────────────────────────────

  Widget _buildTopBar(BuildContext context, VoiceState voiceState) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
      child: Row(
        children: [
          // Back / close button.
          _CircleButton(
            icon: Icons.arrow_back_ios_new,
            onTap: () {
              ref.read(voiceProvider.notifier).endSession();
              context.pop();
            },
          ),
          const SizedBox(width: 16),
          // Title column.
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'आवाजमा कुराकानी',
                  style: TextStyle(
                    fontSize: 19,
                    fontWeight: FontWeight.bold,
                    color: AppColors.ink,
                  ),
                ),
                Text(
                  _statusLabel(voiceState.status),
                  style: const TextStyle(
                    fontSize: 12.5,
                    color: AppColors.muted,
                  ),
                ),
              ],
            ),
          ),
          // Language toggle.
          GestureDetector(
            onTap: _toggleLanguage,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.75),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.white),
              ),
              child: Text(
                _nepali ? 'नेपाली' : 'English',
                style: const TextStyle(
                  color: AppColors.inkSoft,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Orb area ─────────────────────────────────────────────────────────────

  Widget _buildOrbArea(VoiceState voiceState) {
    final isListening = voiceState.status == VoiceConversationState.listening;
    final isProcessing =
        voiceState.status == VoiceConversationState.processing ||
            voiceState.status == VoiceConversationState.responding;

    return Center(
      child: GestureDetector(
        onTap: () => _handleOrbTap(voiceState.status),
        child: AnimatedBuilder(
          animation: _pulseAnim,
          builder: (context2, anim) {
            final scale = isListening ? _pulseAnim.value : 1.0;
            return Transform.scale(
              scale: scale,
              child: Container(
                width: 200,
                height: 200,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: _orbGradient(voiceState.status),
                  boxShadow: [
                    BoxShadow(
                      color: _orbGlowColor(voiceState.status),
                      blurRadius: isListening ? 60 : 40,
                      spreadRadius: isListening ? 10 : -5,
                      offset: const Offset(0, 15),
                    ),
                  ],
                ),
                child: Center(
                  child: isProcessing
                      ? const SizedBox(
                          width: 36,
                          height: 36,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 3,
                          ),
                        )
                      : Icon(
                          _orbIcon(voiceState.status),
                          color: Colors.white,
                          size: 56,
                        ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  // ── Transcript area ──────────────────────────────────────────────────────

  Widget _buildTranscriptArea(VoiceState voiceState) {
    final hasTranscript = voiceState.partialTranscript.isNotEmpty;
    final isListening = voiceState.status == VoiceConversationState.listening;
    final hasError = voiceState.status == VoiceConversationState.error;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 8.0),
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 200),
        child: hasError
            ? Container(
                key: const ValueKey('error'),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.red.withValues(alpha: 0.3)),
                ),
                child: Text(
                  voiceState.errorMessage ?? 'त्रुटि भयो।',
                  style:
                      const TextStyle(color: Colors.red, fontSize: 14, height: 1.4),
                  textAlign: TextAlign.center,
                ),
              )
            : hasTranscript && isListening
                ? _buildTranscriptCard(voiceState.partialTranscript)
                : const SizedBox(height: 48, key: ValueKey('empty')),
      ),
    );
  }

  Widget _buildTranscriptCard(String transcript) {
    return Container(
      key: const ValueKey('transcript'),
      constraints: const BoxConstraints(minHeight: 48),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.75),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white),
      ),
      child: Row(
        children: [
          const Icon(Icons.mic, color: AppColors.purple1, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              transcript,
              style: const TextStyle(
                fontSize: 16,
                color: AppColors.ink,
                fontWeight: FontWeight.w500,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Last AI message preview ──────────────────────────────────────────────

  Widget _buildLastAiMessage(ChatState chatState) {
    final aiMessages = chatState.messages.where((m) => !m.isUser).toList();
    if (aiMessages.isEmpty) return const SizedBox.shrink();

    final last = aiMessages.last;
    final displayText = last.structuredAnswer?.message.isNotEmpty == true
        ? last.structuredAnswer!.message
        : last.content;

    if (displayText.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 4.0),
      child: Container(
        constraints: const BoxConstraints(maxHeight: 88),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.65),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.cardBorder),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('🤖 ', style: TextStyle(fontSize: 14)),
            Expanded(
              child: Text(
                displayText,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 13,
                  color: AppColors.inkSoft,
                  height: 1.4,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Bottom control bar ───────────────────────────────────────────────────

  Widget _buildBottomBar(VoiceState voiceState) {
    final status = voiceState.status;
    final isEnded = status == VoiceConversationState.ended ||
        status == VoiceConversationState.idle;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 20.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Keyboard / typed-chat shortcut.
          _CircleButton(
            icon: Icons.keyboard_alt_outlined,
            onTap: () {
              ref.read(voiceProvider.notifier).endSession();
              context.go('/chat');
            },
          ),
          const SizedBox(width: 22),
          // Primary action button.
          GestureDetector(
            onTap: () => _handleOrbTap(status),
            child: Container(
              width: 76,
              height: 76,
              decoration: BoxDecoration(
                gradient: isEnded
                    ? const LinearGradient(
                        colors: [Color(0xFF6D7CF5), Color(0xFF3A3FBF)])
                    : status == VoiceConversationState.listening
                        ? const LinearGradient(
                            colors: [Color(0xFFE53E3E), Color(0xFFC53030)])
                        : status == VoiceConversationState.speaking
                            ? const LinearGradient(
                                colors: [Color(0xFF38A169), Color(0xFF2F855A)])
                            : const LinearGradient(
                                colors: [AppColors.muted, AppColors.inkSoft]),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: const Color(0x268B7BF5),
                    spreadRadius: 8,
                  ),
                  const BoxShadow(
                    color: Color(0x993C3CB4),
                    blurRadius: 30,
                    offset: Offset(0, 14),
                    spreadRadius: -10,
                  ),
                ],
              ),
              child: Icon(
                isEnded
                    ? Icons.mic_none
                    : status == VoiceConversationState.listening
                        ? Icons.stop
                        : status == VoiceConversationState.speaking
                            ? Icons.volume_up
                            : Icons.hourglass_top,
                color: Colors.white,
                size: 30,
              ),
            ),
          ),
          const SizedBox(width: 22),
          // Close button.
          _CircleButton(
            icon: Icons.close,
            onTap: () {
              ref.read(voiceProvider.notifier).endSession();
              context.pop();
            },
          ),
        ],
      ),
    );
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  String _statusLabel(VoiceConversationState s) {
    switch (s) {
      case VoiceConversationState.idle:
        return 'ट्याप गर्नुहोस्';
      case VoiceConversationState.initializing:
        return 'सुरु हुँदैछ…';
      case VoiceConversationState.listening:
        return '🎤 सुन्दैछ…';
      case VoiceConversationState.processing:
        return '⏳ प्रक्रिया गर्दैछ…';
      case VoiceConversationState.responding:
        return '🔄 जवाफ आउँदैछ…';
      case VoiceConversationState.speaking:
        return '🔊 बोल्दैछ…';
      case VoiceConversationState.error:
        return 'त्रुटि भयो';
      case VoiceConversationState.ended:
        return 'रोकिएको छ';
    }
  }

  IconData _orbIcon(VoiceConversationState s) {
    switch (s) {
      case VoiceConversationState.listening:
        return Icons.mic;
      case VoiceConversationState.speaking:
        return Icons.volume_up;
      case VoiceConversationState.error:
        return Icons.error_outline;
      case VoiceConversationState.ended:
      case VoiceConversationState.idle:
        return Icons.mic_none;
      default:
        return Icons.hourglass_top;
    }
  }

  Gradient _orbGradient(VoiceConversationState s) {
    switch (s) {
      case VoiceConversationState.listening:
        return const RadialGradient(
          center: Alignment(-0.3, -0.4),
          colors: [Color(0xFF6D7CF5), Color(0xFF3A3FBF)],
          radius: 0.7,
        );
      case VoiceConversationState.speaking:
        return const RadialGradient(
          center: Alignment(-0.3, -0.4),
          colors: [Color(0xFF48BB78), Color(0xFF2F855A)],
          radius: 0.7,
        );
      case VoiceConversationState.error:
        return const RadialGradient(
          colors: [Color(0xFFFC8181), Color(0xFFE53E3E)],
          radius: 0.7,
        );
      default:
        return const RadialGradient(
          center: Alignment(-0.3, -0.4),
          colors: [Color(0xFFBDB5E8), Color(0xFF8B7BF5)],
          radius: 0.7,
        );
    }
  }

  Color _orbGlowColor(VoiceConversationState s) {
    switch (s) {
      case VoiceConversationState.listening:
        return const Color(0x408B7BF5);
      case VoiceConversationState.speaking:
        return const Color(0x4038A169);
      default:
        return const Color(0x203C3CB4);
    }
  }
}

// ── Small helper widget ───────────────────────────────────────────────────────

class _CircleButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _CircleButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.75),
          shape: BoxShape.circle,
          border: Border.all(color: Colors.white),
        ),
        child: Icon(icon, color: AppColors.inkSoft, size: 20),
      ),
    );
  }
}

import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import '../../../shared/widgets/sahayak_widgets.dart';
import '../../../app/theme/sahayak_theme.dart';
import '../../../core/constants/app_limits.dart';
import '../widgets/voice_send.dart';

/// HTML Screen 3 — voice conversation (`आवाजमा कुराकानी`).
///
/// States (matching the mockup's three controls):
///   idle            → big mic, keyboard + cancel round buttons
///   recording       → orb pulses, timer counts toward the 30 s cap
///   sending         → orb shows progress, controls disabled
///   error           → friendly inline message, back to idle
class VoiceScreen extends HookConsumerWidget {
  final String sessionId;

  const VoiceScreen({super.key, required this.sessionId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recorder = useMemoized(() => AudioRecorder());
    final phase = useState<_VoicePhase>(_VoicePhase.idle);
    final elapsed = useState(0);
    final errorMessage = useState<String?>(null);
    final timer = useRef<Timer?>(null);

    useEffect(() {
      return () {
        timer.value?.cancel();
        recorder.dispose();
      };
    }, []);

    late final Future<void> Function() stopAndSend;

    Future<void> start() async {
      if (phase.value != _VoicePhase.idle) return;
      errorMessage.value = null;
      try {
        final hasPermission = await recorder.hasPermission();
        if (!hasPermission) {
          errorMessage.value =
              'भ्वाइस मेसेज पठाउन माइक्रोफोन अनुमति चाहिन्छ।';
          return;
        }
        final tempDir = await getTemporaryDirectory();
        final path =
            '${tempDir.path}/sahayak_voice_${DateTime.now().millisecondsSinceEpoch}.wav';
        await recorder.start(
          const RecordConfig(
            encoder: AudioEncoder.wav,
            sampleRate: 16000,
            numChannels: 1,
          ),
          path: path,
        );
        elapsed.value = 0;
        phase.value = _VoicePhase.recording;
        timer.value = Timer.periodic(const Duration(seconds: 1), (t) {
          elapsed.value += 1;
          if (elapsed.value >= AppLimits.maxAudioDurationSec) {
            stopAndSend();
          }
        });
      } catch (_) {
        errorMessage.value = 'रेकर्डिङ सुरु गर्न सकिएन। फेरि प्रयास गर्नुहोस्।';
        phase.value = _VoicePhase.idle;
      }
    }

    Future<void> stopAndSendImpl() async {
      // Capture the router before any await so nothing uses `context` across
      // an async gap.
      final router = GoRouter.of(context);
      if (phase.value != _VoicePhase.recording) return;
      timer.value?.cancel();
      final path = await recorder.stop();
      phase.value = _VoicePhase.sending;
      if (path == null || path.isEmpty) {
        errorMessage.value = 'रेकर्डिङ सेभ गर्न सकिएन।';
        phase.value = _VoicePhase.idle;
        return;
      }
      final error = await sendVoiceFileWithRef(ref, sessionId, path);
      if (error != null) {
        errorMessage.value = error;
        phase.value = _VoicePhase.idle;
        return;
      }
      // Success: leave this screen; chat shows the reply.
      router.pushReplacement('/chat/$sessionId');
    }
    stopAndSend = stopAndSendImpl;

    final recording = phase.value == _VoicePhase.recording;
    final sending = phase.value == _VoicePhase.sending;
    final busy = recording || sending;
    final remaining = AppLimits.maxAudioDurationSec - elapsed.value;

    return Scaffold(
      body: SahayakBackground(
        variant: SahayakBgVariant.voice,
        child: SafeArea(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
                child: Column(
                  children: [
                    // .s3-top
                    Row(
                      children: [
                        FrostedCircleButton(
                          semanticLabel: 'Back',
                          onTap: busy ? null : () => context.pop(),
                          size: 38,
                          child: const Icon(Icons.chevron_left, size: 22),
                        ),
                        const SizedBox(width: 16),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('आवाजमा कुराकानी',
                                style: Theme.of(context).textTheme.titleLarge),
                            Text(
                              sending
                                  ? 'पठाइँदैछ…'
                                  : recording
                                      ? 'सुनिँदैछ… ${remaining}s बाँकी'
                                      : 'भन्नुहोस्, म सुन्दैछु…',
                              style: const TextStyle(
                                  fontSize: 12.5,
                                  color: SahayakColors.muted),
                            ),
                          ],
                        ),
                      ],
                    ),
                    if (errorMessage.value != null) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Theme.of(context)
                                  .colorScheme
                                  .error
                                  .withValues(alpha: .10),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.error_outline,
                                size: 18,
                                color: Theme.of(context).colorScheme.error),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(errorMessage.value!,
                                  style: TextStyle(
                                      fontSize: 13,
                                      color:
                                          Theme.of(context).colorScheme.error)),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              // .s3-orb-wrap
              Expanded(
                child: Center(
                  child: _VoiceOrb(recording: recording, sending: sending),
                ),
              ),
              // .s3-quote
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
                child: Text(
                  recording
                      ? '"मेरो जग्गाको समस्या छ।"\nअब के गर्ने होला?'
                      : '"मेरो जग्गाको समस्या छ।"\nअब के गर्ने होला?',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w600,
                      height: 1.55,
                      color: SahayakColors.ink),
                ),
              ),
              // .s3-bottom
              Padding(
                padding: const EdgeInsets.only(bottom: 26),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    FrostedCircleButton(
                      semanticLabel: 'Type instead',
                      onTap: busy
                          ? null
                          : () => context.pushReplacement('/chat/$sessionId'),
                      child: const Icon(Icons.keyboard_alt_outlined, size: 20),
                    ),
                    const SizedBox(width: 22),
                    Semantics(
                      button: true,
                      label: recording
                          ? 'Stop and send recording'
                          : 'Hold or tap to record',
                      child: GestureDetector(
                        onTap: sending ? null : () => recording ? stopAndSend() : start(),
                        child: Container(
                          width: 76,
                          height: 76,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: SahayakColors.micGradient,
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF8b7bf5).withValues(alpha: .15),
                                blurRadius: 0,
                                spreadRadius: 8,
                              ),
                              BoxShadow(
                                color: const Color(0xFF3c3cb4).withValues(alpha: .55),
                                blurRadius: 30,
                                offset: const Offset(0, 14),
                                spreadRadius: -10,
                              ),
                            ],
                          ),
                          child: Center(
                            child: sending
                                ? const SizedBox(
                                    width: 26,
                                    height: 26,
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2.5,
                                        color: Colors.white))
                                : Icon(
                                    recording ? Icons.stop : Icons.mic,
                                    color: Colors.white,
                                    size: 26,
                                  ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 22),
                    FrostedCircleButton(
                      semanticLabel: 'Cancel',
                      onTap: busy ? null : () => context.pop(),
                      child: const Icon(Icons.close, size: 20),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

enum _VoicePhase { idle, recording, sending }

/// Animated gradient orb (`.s3-orb`) — soft blurred color blobs that breathe
/// while recording.
class _VoiceOrb extends StatefulWidget {
  final bool recording;
  final bool sending;
  const _VoiceOrb({required this.recording, required this.sending});

  @override
  State<_VoiceOrb> createState() => _VoiceOrbState();
}

class _VoiceOrbState extends State<_VoiceOrb>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 2600),
  );

  @override
  void initState() {
    super.initState();
    _controller.repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final t = _controller.value;
        final scale = widget.recording
            ? 1.0 + 0.05 * math.sin(t * 2 * math.pi)
            : 1.0 + 0.02 * math.sin(t * 2 * math.pi);
        return SizedBox(
          width: 270,
          height: 270,
          child: ScaleTransition(
            scale: AlwaysStoppedAnimation(scale),
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Outer shadow ring
                Container(
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Theme.of(context).brightness == Brightness.dark
                        ? const Color(0xFF232335)
                        : const Color(0xFFeef1f7),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF3c3c6e).withValues(alpha: .35),
                        blurRadius: 50,
                        offset: const Offset(0, 20),
                        spreadRadius: -20,
                      ),
                    ],
                  ),
                ),
                // Blurred color blobs (rotating) — CSS ::before
                ClipOval(
                  child: SizedBox(
                    width: 270,
                    height: 270,
                    child: Transform.rotate(
                      angle: t * 2 * math.pi * (widget.recording ? 1 : 0.15),
                      child: Stack(
                        children: [
                          Positioned(
                            left: 40,
                            top: 30,
                            child: _blob(160, const Color(0xFF4b5eea)),
                          ),
                          Positioned(
                            right: 40,
                            top: 90,
                            child: _blob(150, const Color(0xFF8b5cf6)),
                          ),
                          Positioned(
                            left: 60,
                            bottom: 50,
                            child: _blob(130, const Color(0xFFf3f0fa)),
                          ),
                          Positioned(
                            right: 50,
                            top: 10,
                            child: _blob(110, const Color(0xFFd7c8f7)),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                if (widget.sending)
                  const SizedBox(
                    width: 34,
                    height: 34,
                    child: CircularProgressIndicator(
                        strokeWidth: 3, color: Colors.white),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _blob(double size, Color color) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(
          colors: [color.withValues(alpha: .95), color.withValues(alpha: 0)],
        ),
      ),
    );
  }
}

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

const int kMaxRecordingSeconds = 30;

/// Hold-to-record microphone button.
///
/// Records 16 kHz mono WAV, which is one of the two formats accepted by the
/// Sahayak backend (`audio/wav`). The other accepted format is MP3.
class VoiceRecordButton extends HookWidget {
  final ValueChanged<String> onRecordingComplete;
  final bool enabled;

  const VoiceRecordButton({
    super.key,
    required this.onRecordingComplete,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    final recorder = useMemoized(() => AudioRecorder());
    final isRecording = useState(false);
    final elapsed = useState(0);
    final timer = useRef<Timer?>(null);

    useEffect(() {
      return () {
        timer.value?.cancel();
        recorder.dispose();
      };
    }, []);

    Future<void> stop() async {
      if (!isRecording.value) return;
      timer.value?.cancel();
      isRecording.value = false;
      final path = await recorder.stop();
      if (path != null && path.isNotEmpty) {
        onRecordingComplete(path);
      }
    }

    Future<void> start() async {
      if (!enabled || isRecording.value) return;
      try {
        final hasPermission = await recorder.hasPermission();
        if (!hasPermission) {
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text(
                  'Microphone permission is required to send a voice message.',
                ),
              ),
            );
          }
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
        isRecording.value = true;
        timer.value = Timer.periodic(const Duration(seconds: 1), (t) {
          elapsed.value += 1;
          if (elapsed.value >= kMaxRecordingSeconds) {
            stop();
          }
        });
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Could not start recording: $e')),
          );
        }
      }
    }

    final recordColor = isRecording.value
        ? Theme.of(context).colorScheme.error
        : Theme.of(context).colorScheme.surfaceContainerHighest;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (isRecording.value)
          Padding(
            padding: const EdgeInsets.only(right: 6),
            child: Text(
              '${kMaxRecordingSeconds - elapsed.value}s',
              style: TextStyle(
                color: Theme.of(context).colorScheme.error,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        Semantics(
          button: true,
          label: isRecording.value
              ? 'Recording, release to send'
              : 'Hold to record a voice message',
          child: GestureDetector(
            onLongPressStart: enabled && !isRecording.value
                ? (_) => start()
                : null,
            onLongPressEnd: isRecording.value ? (_) => stop() : null,
            onLongPressCancel: isRecording.value ? stop : null,
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: recordColor,
                shape: BoxShape.circle,
              ),
              child: Icon(
                isRecording.value ? Icons.mic : Icons.mic_none,
                color: isRecording.value
                    ? Theme.of(context).colorScheme.onError
                    : (enabled
                          ? Theme.of(context).colorScheme.onSurfaceVariant
                          : Theme.of(context).disabledColor),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

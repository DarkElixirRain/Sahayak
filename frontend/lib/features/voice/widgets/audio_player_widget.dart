import 'dart:convert';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:path_provider/path_provider.dart';

/// Plays a base64-encoded audio clip returned by the backend.
///
/// If the clip cannot be decoded or loaded (for example the development
/// backend returns dummy bytes when no real TTS provider is configured),
/// this widget renders nothing instead of an endless spinner.
class AudioPlayerWidget extends HookWidget {
  final String base64Audio;

  const AudioPlayerWidget({super.key, required this.base64Audio});

  @override
  Widget build(BuildContext context) {
    final player = useMemoized(() => AudioPlayer());
    final isPlaying = useState(false);
    final isLoaded = useState(false);
    final isFailed = useState(false);
    final duration = useState(Duration.zero);
    final position = useState(Duration.zero);

    useEffect(() {
      var disposed = false;

      Future<void> prepareAudio() async {
        try {
          final bytes = base64Decode(base64Audio);
          if (bytes.length < 64) {
            // Too small to be real audio (mock TTS is a few bytes).
            if (!disposed) isFailed.value = true;
            return;
          }
          final tempDir = await getTemporaryDirectory();
          final file = File(
            '${tempDir.path}/sahayak_tts_${DateTime.now().millisecondsSinceEpoch}.mp3',
          );
          await file.writeAsBytes(bytes, flush: true);
          await player.setSourceDeviceFile(file.path);
          if (!disposed) isLoaded.value = true;
        } catch (_) {
          if (!disposed) isFailed.value = true;
        }
      }

      prepareAudio();

      final durationSub = player.onDurationChanged.listen((d) {
        duration.value = d;
      });
      final positionSub = player.onPositionChanged.listen((p) {
        position.value = p;
      });
      final stateSub = player.onPlayerStateChanged.listen((s) {
        isPlaying.value = s == PlayerState.playing;
      });

      return () {
        disposed = true;
        durationSub.cancel();
        positionSub.cancel();
        stateSub.cancel();
        player.dispose();
      };
    }, [base64Audio]);

    if (isFailed.value) return const SizedBox.shrink();
    if (!isLoaded.value) {
      return const Padding(
        padding: EdgeInsets.all(8.0),
        child: SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      );
    }

    final maxMs = duration.value.inMilliseconds > 0
        ? duration.value.inMilliseconds.toDouble()
        : 1.0;
    final currentMs = position.value.inMilliseconds
        .clamp(0, maxMs.toInt())
        .toDouble();

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton(
          tooltip: isPlaying.value ? 'Pause' : 'Play',
          icon: Icon(isPlaying.value ? Icons.pause : Icons.play_arrow),
          onPressed: () {
            if (isPlaying.value) {
              player.pause();
            } else {
              player.resume();
            }
          },
        ),
        Flexible(
          child: Slider(
            value: currentMs,
            min: 0,
            max: maxMs,
            onChanged: (value) {
              player.seek(Duration(milliseconds: value.toInt()));
            },
          ),
        ),
      ],
    );
  }
}

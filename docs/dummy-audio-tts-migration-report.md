# Dummy Audio TTS Migration Report

**Date:** 2026-09-20
**Scope:** Sahayak voice-conversation flow — replace live text-to-speech (TTS) with playback of a single pre-recorded dummy audio file while preserving speech-to-text, AI text response, and chat functionality.

## 1. Objective

The dynamic TTS pipeline (ElevenLabs) in the mobile voice conversation flow is out of scope / unavailable for the current milestone. The system is migrated to a **dummy audio playback** model:

- The backend no longer synthesises speech. It serves one hard-coded MP3 stored in Morphik backend storage and reports its URL in the query response as `audio_url`.
- The Flutter app automatically plays that audio (`DummyAudioService` → `audioplayers`) after each AI response inside the voice conversation, and automatically resumes listening when playback finishes.
- The voice button, microphone permission, speech-to-text, AI text response, and chat history are **unchanged**.

The `AudioService` abstraction keeps the door open for a future real TTS: swap the concrete `DummyAudioService` for a `RealTTSService` without touching `VoiceNotifier`.

## 2. Files Inspected

- Backend: `core/api.py`, `core/models/completion.py`, `core/routes/audio.py` (new), `core/routes/documents.py`, `core/routes/query.py`, `core/services_init.py`, `core/storage/local_storage.py`, `core/storage/base.py`, `core/settings_morphik.py`, `morphik.toml`, `storage/<dummy mp3>`.
- Flutter: `pubspec.yaml`, `pubspec.lock`, `lib/core/config.dart`, `lib/api/chat_api.dart`, `lib/core/services/*`, `lib/features/voice/domain/voice_notifier.dart`, `lib/features/voice/presentation/voice_screen.dart`, `lib/features/chat/presentation/chat_provider.dart`, `lib/shared/models/chat_models.dart`, `lib/features/voice/domain/speech_service.dart`, `lib/features/voice/domain/answer_to_speech.dart`, `test/shared/models/chat_models_test.dart`.
- Confirmed **no existing TTS/audio code** in the backend.

## 3. Files Changed

### Backend
- `core/models/completion.py` — added `audio_url: Optional[str] = None` to `CompletionResponse`.
- `core/routes/audio.py` — **new**. Router prefix `/audio`. Endpoint `GET /audio/dummy-response` serves the dummy MP3 from Morphik storage (`document_service.storage.download_file("", DUMMY_RESPONSE_AUDIO_KEY)`) with `Content-Type: audio/mpeg`, `Content-Length`, `Content-Disposition`, and `Cache-Control: public, max-age=3600`. Returns 404 if the file is missing.
  - Constants: `DUMMY_RESPONSE_AUDIO_URL = "/audio/dummy-response"`, `DUMMY_RESPONSE_AUDIO_KEY`, `DUMMY_RESPONSE_AUDIO_MEDIA_TYPE = "audio/mpeg"`.
- `core/api.py` — registered the audio router and set `audio_url=DUMMY_RESPONSE_AUDIO_URL` on the casual-greeting `CompletionResponse` and on the non-streaming `/query` response before returning.

### Flutter
- `pubspec.yaml` — removed `flutter_tts: ^4.2.1`; added `audioplayers: ^6.8.1` (`pubspec.lock` updated).
- `lib/core/services/audio_service.dart` — **new**. Abstract `AudioService` contract: `isPlaying`, `onPlaybackComplete`, `onPlaybackError`, `play(String audioUrl)`, `stop()`, `dispose()`.
- `lib/core/services/dummy_audio_service.dart` — **new**. `DummyAudioService` (implements `AudioService`) using a single `AudioPlayer` (audioplayers 6.8.1). Resolves relative URLs against `AppConfig.baseUrl`. `stop()` sets an internal flag so a deliberate interruption never emits `onPlaybackComplete`. Play failures and empty/invalid URLs emit an error and a completion so the caller can resume.
- `lib/core/services/tts_service.dart` — **deleted** (real TTS removed along with the `flutter_tts` package).
- `lib/shared/models/chat_models.dart` — `QueryResponse.audioUrl` parsed from `json['audio_url']`; optional `audioUrl` field on `ChatMessage`.
- `lib/features/chat/presentation/chat_provider.dart` — AI `ChatMessage` now carries `audioUrl: response.audioUrl`.
- `lib/features/voice/domain/voice_notifier.dart` — **rewritten** to drive dummy audio playback instead of TTS:
  - `audioServiceProvider` provides `DummyAudioService`.
  - `answerToSpeech`/TTS calls removed; `answer_to_speech.dart` left in place (unused) for a future real TTS.
  - `_forwardToChat` plays `lastAi.audioUrl` when present; otherwise shows a transient "आडियो उपलब्ध छैन।" message before resuming listening.
  - `_onPlaybackComplete` / audio error handling resume listening; `interrupt()`/`endSession()`/cleanup call `AudioService.stop()`.

## 4. Why TTS Is Disabled (Not Enabled)

- The previous `FlutterTtsService` used the `flutter_tts` plugin, which synthesises speech **on-device** (or needs a TTS engine) and has proven unreliable/problematic in this environment (e.g., engine missing, long Latin-script strings, inconsistent silence auto-detection for resuming listening).
- Backend TTS (ElevenLabs) was never implemented in the backend codebase.
- For the current milestone a deterministic, always-available "AI responded with audio" behaviour is required for demos, so a pre-recorded clip is served instead.

## 5. Dummy Audio Location / Access / Endpoint / Loading

### Location
- Backend storage root: `Sahayak/backend/storage/`.
- File: `ElevenLabs_2026-09-20T01_29_55_Roger - Laid-Back, Casual, Resonant_pre_sp100_s50_sb75_se0_b_m2.mp3`.
- Media type `audio/mpeg`; size 794,470 bytes; 1 channel, 44.1 kHz, 128 kbps, ~48.6 s.
- Referenced by constant `DUMMY_RESPONSE_AUDIO_KEY` (verbatim filename). Morphik local storage is configured via `morphik.toml` → `[storage] provider="local", storage_path="./storage"`.

### Endpoint
- `GET /audio/dummy-response` → returns the MP3 with `Content-Type: audio/mpeg` and `Cache-Control: public, max-age=3600`.
- The relative URL `/audio/dummy-response` is what the backend embeds in `CompletionResponse.audio_url`.

### How the Flutter app loads it
1. Chat API response is parsed (`QueryResponse.fromJson`) into `audioUrl`.
2. `VoiceNotifier._forwardToChat` asks `AudioService.play(audioUrl)`.
3. `DummyAudioService` builds `Uri.parse(AppConfig.baseUrl).resolve(audioUrl)` (e.g., `http://10.10.60.158:8000/audio/dummy-response`) and plays via `AudioPlayer.play(UrlSource(...))`.
4. The player streams/buffers the MP3 over HTTP; playback completes naturally → `onPlayerComplete` → the notifier resumes the microphone.

### Security
- The dummy-audio endpoint is deliberately **public** (no `verify_token`) because `audioplayers` cannot attach JWT headers to the media request. It is safe because it serves only one hard-coded key — it never accepts an arbitrary path. The current deployment also uses `bypass_auth_mode = true` for the demo.

## 6. Voice Flow (STT → AI → Text → Dummy Audio → Playback)

1. User taps the voice button → `VoiceScreen` → `SpeechService` (speech_to_text) starts listening.
2. On recognized speech → `VoiceNotifier` sends the text to the chat API (`sendMessage`).
3. AI responds; backend sets `audio_url` on the response.
4. The AI completion text is appended to the conversation as a `ChatMessage` (with `audioUrl`).
5. `VoiceNotifier` transitions to the `speaking` state and calls `AudioService.play(audioUrl)`.
6. The dummy MP3 plays (~48 s) — the "बोल्दैछ…" indicator is shown.
7. On playback completion (or audio error), `VoiceNotifier` returns to listening.
8. If no `audio_url` is present (e.g., a future backend config), a transient "आडियो उपलब्ध छैन।" message is shown and listening resumes after ~800 ms. The text answer is always preserved in chat.

## 7. Actual Verification Run

### Backend
- `python -m py_compile core/api.py core/routes/audio.py core/models/completion.py` — OK.
- App import (venv311, Python 3.11): `from core.api import app` — OK; registered routes include `/audio/dummy-response` and `/query`.
- Functional check of the audio route (TestClient): `GET /audio/dummy-response` → 200, `Content-Type: audio/mpeg`, `Content-Length: 794470`; missing-file case → 404.
- `CompletionResponse` model: `audio_url` serializes (`"audio_url":"/audio/dummy-response"`) and defaults to `null` when absent.
- Test suite: `./venv311/bin/python -m pytest core/tests/unit/test_metadata_filters.py core/tests/unit/test_typed_metadata.py core/tests/unit/test_morphik_graph_service.py` → **91 passed, 15 warnings**.
- Note: a bare `TestClient` POST to `/query` returns 500 because `get_redis_pool` requires Redis, which is started in FastAPI's lifespan (not exercised outside a live server) — this is **pre-existing** and unrelated to the audio change.

### Flutter (Dart 3.12.2, Flutter 3.44.4 stable)
- `flutter pub get` — OK; `audioplayers 6.8.1` resolved; `flutter_tts` removed from `pubspec.lock`.
- `flutter analyze` — **0 errors** from this change. Remaining 17 findings are pre-existing and untouched: deprecated `withOpacity` usages in `chat_screen.dart`, `home_screen.dart`, `onboarding_screen.dart`, and two unused private helpers in `home_screen.dart`.
- `flutter test` — **8 passed** (chat model tests, including new `audio_url` parse + null-default cases).
- `flutter build apk --debug` — **build succeeds** with audioplayers and without flutter_tts.

### Not executed / not applicable
- No live end-to-end run on a physical device/emulator with voice input + audio playback performed.
- No changes to `core/tests/unit` collection failures for `test_reranker.py` / `test_colpali_embedding.py` / `test_multivector.py` (missing optional `FlagEmbedding`/torch deps — pre-existing).
- `venv310` still has a pre-existing `datetime.UTC` import error; Python 3.11 (`./venv311`) is the canonical backend environment.

## 8. Potential Issues / Remaining Limitations

- The **same recording** plays for every AI response regardless of the actual answer text. This is the core trade-off of the dummy-audio milestone.
- Long Latin/English strings are no longer read aloud by the system (no on-device TTS). If a real TTS come back, restore `answer_to_speech.dart` usage or a real backend TTS and swap the `AudioService` implementation.
- In iOS/macOS builds, HTTP (non-TLS) streaming to a LAN IP requires ATS exceptions already configured in the app; Android debug builds default is fine.
- `audioplayers` buffers the MP3 over HTTP on first request, so the first playback can take a moment depending on the network.
- Auto-resume relies on the notifier's state machine; during the ~48 s playback the microphone is intentionally muted to avoid playback leaking into STT.
- No automated widget/integration test for the voice screen exists in the repo; only model-level tests were added.
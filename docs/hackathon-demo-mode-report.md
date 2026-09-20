# Sahayak / Kanun Sathi — Hackathon Demo Mode Report

Date: 2026-09-20

This report documents the offline "demo mode" that powers the full Sahayak
presentation flow with the backend, database, Redis, and external services
completely stopped.

---

## 1. Overview

Sahayak now ships with a central master switch — `DemoConfig.demoMode` — which
defaults to **ON** so the packaged builds run fully offline. When enabled, every
feature (auth, chat, voice, search, saved items, cases, notifications, profile,
settings) is served by a local demo data layer plus a deterministic local legal
assistant and a bundled local audio recording. When disabled, the original real
backend stack (FastAPI + Redis + Morphik + LLM) is used unchanged.

```
flutter run --dart-define=DEMO_MODE=false   # real backend mode (default is demo)
```

Everything consumed by the UI lives behind the existing repository/provider
interfaces; the UI cannot tell (and never displays) whether the source is the
demo layer or the real backend. No labels, badges, or tooltips expose the demo
nature to a presentation audience.

## 2. Architecture

```
UI (home / chat / voice / search / saved / cases / notifications / profile / settings)
  │
  ├── AuthProvider ────── demo: auto-authenticate (no token, no storage)
  ├── ChatRepository ──── demo: local seeded history + offline answers
  ├── VoiceNotifier ───── demo: real on-device speech-to-text (SpeechToTextService)
  │                        demo assistant answer → local audio playback (asset)
  │                        NEVER calls the backend directly
  └── DemoRepository ──── ChangeNotifier (legacy Riverpod provider)
        ├── DemoData (static seed content, read-only)
        ├── DemoAssistantService (deterministic keyword scenario engine)
        └── Simulated 600ms latency → believable UX
```

Key files (Flutter, `Sahayak/mobile`):

| File | Purpose |
| --- | --- |
| `lib/core/demo/demo_config.dart` | Central flag, demo account, `asset://` audio marker, delays |
| `lib/core/demo/demo_models.dart` | `DemoProfile`, `DemoArticle`, `DemoConsultation`, `DemoNotification`, `DemoActivity` |
| `lib/core/demo/demo_data.dart` | Seed profile, 11 guidance articles, saved items, consultations, notifications, activity |
| `lib/core/demo/demo_assistant_service.dart` | Offline keyword/scenario assistant (Nepali + English + Romanized) |
| `lib/core/demo/demo_repository.dart` | Mutable local state + simulated latency; auto `reset()` per launch |
| `lib/features/demo/presentation/demo_*_screen.dart` | Article, Cases, Notifications, Profile, Settings, Search/Saved screens |
| `assets/audio/bank_otp.mp3` | 14 s dedicated bank-OTP warning (banks never ask for OTP) |
| `assets/audio/otp_shared.mp3` | 23 s dedicated "OTP already shared" → act-fast reply |
| `assets/audio/divorce.mp3` | 23 s dedicated divorce / सम्बन्ध विच्छेद guidance |
| `assets/audio/jagga.mp3` | 20 s dedicated land / जग्गा dispute guidance |
| `assets/audio/assistant_response.mp3` | 14 s bundled fallback used for every other voice answer |

Per-scenario selection (STEP 8 audio): `DemoAssistantService._audioAssetFor()`
returns the scenario's own `asset://audio/*.mp3` file — `bankOtp → bank_otp`,
`bankOtpGiven → otp_shared`, `divorce → divorce`, `land → jagga`, and every
other scenario falls back to `assistant_response.mp3`. All references are the
local `asset://` marker, so answers are fully offline.

## 3. Demo features

- **Auth** — no login screen; deterministic demo user `Bishal Chaudhary`. Logout
  works locally (clears session, returns to onboarding).
- **Dashboard** — greeting with unread-notification badge, settings entry,
  profile avatar (long-press = developer-only local-data reset), quick actions
  (Ask Sahayak, Voice, Legal Info, My Cases, Saved), "Recent" cards, and a wide
  rights-guidance card.
- **Chat** — opens already seeded with a realistic bank-OTP consultation; sent
  messages receive a structured legal answer with next steps + audio reference.
- **Voice** — real on-device STT (Nepali/English) → speed is fully local: the
  transcript is answered by the demo assistant and the bundled recording is
  played back with `audioplayers`. Mic is always off during playback.
- **Search / Saved** — local catalog with category chips, keyword search, and
  bookmark toggling backed by local state.
- **Cases / history** — informational consultation records with status chips.
  Status wording ("Guidance Provided", "Under Review", "Information Provided")
  never claims a real-world action was taken.
- **Notifications** — read/unread state, per-item + "mark all read".
- **Settings** — language selector, notification toggle, profile + logout,
  fully local.

## 4. Demo assistant scenarios

Priority-ordered keyword matching supporting Devanagari, English, Romanized
Nepali, and mixed text:

| Input (tested) | Scenario |
| --- | --- |
| `मेरो बैंकबाट फोन आयो र OTP माग्यो।` | bank OTP (don't share) |
| `मैले OTP दिइसकेँ अब के गर्ने?` | OTP already shared → act fast |
| `मलाई अनलाइन ठगी भयो।` | online fraud response |
| `जग्गाको विषयमा विवाद भयो।` | land/property guidance |
| `प्रहरीमा उजुरी कसरी दिने?` | police complaint process |
| `मलाई धम्की दिइरहेको छ।` | threat/harassment safety |
| `घरमा झगडा भयो।` | family dispute |
| `मलाई डिभोर्स चाहिएको छ।` | **divorce** / सम्बन्ध विच्छेद (checked before generic family) |
| `श्रीमतीसँग divorce गर्न चाहन्छु।` | **divorce** (English keyword wins over family keywords) |
| `mero bank bata phone aayo OTP magyo` | romanized bank OTP |
| `malai online thagi bhayo` | romanized online fraud |
| `jagga ko dispute cha` | romanized land |
| `malai divorce chaincha` | romanized divorce |
| `divorce ko process k ho` | romanized divorce (process) |
| `divorce garna sakchu?` | romanized divorce (get help) |
| `I need legal help.` / unknown / empty | clarification + fallback |

**Audio per scenario** — `_audioAssetFor()` swaps the exact recording, so the
SUPPORTED legal answer always carries its own voice:

| Scenario | Audio asset |
| --- | --- |
| bank OTP (don't share) | `assets/audio/bank_otp.mp3` |
| OTP already shared → act fast | `assets/audio/otp_shared.mp3` |
| **divorce / सम्बन्ध विच्छेद** | `assets/audio/divorce.mp3` |
| land / जग्गा dispute | `assets/audio/jagga.mp3` |
| every other scenario | `assets/audio/assistant_response.mp3` (fallback retains offline guarantee) |

## 5. Real-mode preservation

`DEMO_MODE=false` restores the exact pre-demo behavior:

- HTTP client / API base URL untouched; chat + query endpoints unchanged.
- Voice flow still routes through `ChatNotifier.sendMessage` → network
  repository (the audio service resolves relative URLs against the configured
  base URL).
- `flutter_tts` is **not** reintroduced; dummy-audio playback (backend-served
  file or local asset) covers audio in both modes.

## 6. Offline verification (all ran with backend/Redis/Morphik stopped)

| Check | Result |
| --- | --- |
| `flutter analyze` | 0 errors, 0 warnings in demo code (9 pre-existing `withOpacity` infos in untouched files) |
| `flutter test` | 32/32 passed |
| `flutter build web` | success |
| `flutter build apk --debug` | success |
| Full-app widget boot test (`SahayakApp` + ProviderScope) | onboarding → demo auth → dashboard → seeded chat, all offline |
| Search over the 11-article local catalog | results returned after simulated 600 ms |
| Backend suite (regression, unchanged task) | 91 passed |

## 7. Known limitations

- Voice demonstration depends on the device/browser supporting the on-device
  speech recognizer and microphone permission; the bundled audio answers are
  language-agnostic (same recording for every scenario).
- Demo consultation records are informational only and are reset from seed data
  at every app launch for a predictable presentation.
- The voice screen relies on `AudioPlayer.onPlayerComplete`; on platforms where
  asset playback completion isn't reported, the loop auto-resumes listening
  after the configured fallback delay instead.
- `DemoConfig.demoMode` is compile-time via `--dart-define`; changing it
  requires a rebuild, by design, so the demo/trial and real builds are distinct.

## 8. Demo reset

Holding the profile avatar for ~1 second resets all local demo state to its
initial seed (also automatic at every app launch). This keeps repeated
presentations identical without exposing a developer control in the UI.
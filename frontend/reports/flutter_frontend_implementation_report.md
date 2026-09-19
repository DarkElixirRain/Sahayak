# Sahayak Flutter Frontend Implementation Report

## 1. Date

2026-09-19.

## 2. Existing Flutter Architecture

Inspected before any change:

* **Flutter 3.44.4 (stable)**, Dart SDK ^3.12.2
* **State management:** flutter_riverpod 3.4.3 + hooks_riverpod (codegen `@riverpod` providers)
* **Routing:** go_router 14 with an auth-redirect provider (`lib/app/router.dart`)
* **Network:** dio 5 + `dio_client.dart` (JWT bearer interceptor, typed error mapping to
  `AppException` subclasses)
* **Auth:** `AuthNotifier` + `SecureStorageService` (flutter_secure_storage), session
  restoration via `/api/auth/me`
* **Models:** freezed + json_serializable (`ConversationMessage`, `ConversationResponse`,
  `Citation`, `ConversationStatus`) — field names already matched the backend JSON
* **Voice:** `record` (16 kHz mono WAV) + `audioplayers`, hold-to-record button,
  Android `RECORD_AUDIO` + iOS `NSMicrophoneUsageDescription` already configured
* **Screens:** login, register, home, chat, profile (Material default styling, blue seed)
* **Tests:** 3 files (17 tests) — login/register widget tests, model parsing tests

## 3. HTML Design Analysis

Source of truth: `ui/index.html` + `ui/style.css` (3 phone mockups).

**Extracted design tokens (verbatim from `:root` and components):**

| Token | Value | Flutter constant |
|---|---|---|
| `--purple-1` / `--purple-2` | `#7c6cf0` / `#8b7bf5` | `SahayakColors.purple1/purple2` |
| `--orange-1` / `--orange-2` | `#f0784a` / `#f5a35a` | `SahayakColors.orange1/orange2` |
| `--pink-1` / `--pink-2` | `#f0a5c8` / `#f6c9a8` | `SahayakColors.pink1/pink2` |
| `--ink` / `--ink-soft` / `--muted` | `#1e1b2e` / `#4a4560` / `#8b87a0` | `SahayakColors.ink/inkSoft/muted` |
| `--card-bg` / `--card-border` | `#ffffffb0` / `#ffffff80` | `SahayakColors.cardBg/cardBorder` |
| Filled button gradient | `135deg #7c6cf0 → #6a58e0` | `filledBtnGradient` |
| Icon tiles | purple/orange/pink 135° gradients | `purpleIconGradient` etc. |
| Mic button | `radial(#6d7cf5 → #3a3fbf 70%)` + 8px halo | `micGradient` |
| Accent heading | `linear(90deg #7c6cf0 → #c56bd6)` text | `headingGradient` (ShaderMask) |
| Cards | 22px radius, glass border, soft shadow | `GlassCard` (22px), `SahayakColors.glassCard` |
| Bubble corners | `20 20 20 4` | user bubble flipped variant |
| Backgrounds | layered radial pastel washes over `#eef0f5` | `SahayakBackground` (3 variants) |
| Fonts | Noto Sans Devanagari 400–800 + Inter | **Bundled Noto Sans Devanagari 400/500/600/700/800** (OFL license) |

**Per-screen analysis:**

* **Screen 1 (onboarding):** gradient heading "तपाईंको आफ्नै कानुनी साथी सहायक" (last word
  gradient), "म साथमा छु।" bubble (corners 20/20/20/4) + 3 typing dots, a **robot mascot built
  entirely from CSS shapes** (head 160×130 rounded 50%/50%/46%/46%, visor `#182238` radius 30
  with two 26px orange-glow eyes and teal mouth, body with 3 panel dots, rotated arms, dark
  hands/feet), CTA pill `.s1-cta` (44px gradient circle + gradient label + `»`), home indicator.
* **Screen 2 (home):** topbar (42px bot avatar with glowing eyes, greeting stack, सहायता chip),
  "म कसरी सहयोग गरूँ?" heading, 2-card grid (purple chat card with filled button, orange mic
  card with ghost button), wide pink rights card, "यस सत्रको कुराकानी" subhead with "सबै",
  `.session-item` rows with `›`.
* **Screen 3 (voice):** back circle + title stack "आवाजमा कुराकानी / भन्नुहोस्, म सुन्दैछु…",
  **270px orb** (CSS `::before` with 4 blurred radial blobs #4b5eea/#8b5cf6/#f3f0fa/#d7c8f7),
  quote text, bottom controls: keyboard round button, 76px mic with halo shadow, ✕ round button.

**Responsive behavior:** the HTML is a fixed-width phone mockup (352×762) — it does not define
desktop/tablet layouts. I therefore implemented a single adaptive column that centers content
with a max width (520 home / 760 chat) and scales down naturally for phones, rather than
inventing layouts the design doesn't specify. Status bar and home-indicator are OS chrome and
intentionally not reproduced.

## 4. Flutter Implementation

Created:

| File | Purpose |
|---|---|
| `lib/app/theme/sahayak_theme.dart` | Design system: all colors/gradients from style.css, `SahayakBackground` (3 screen variants), `buildSahayakTheme` light+dark |
| `lib/shared/widgets/sahayak_widgets.dart` | `GlassCard`, `GradientIconTile`, `GoPillButton`, `FrostedCircleButton`, `BotAvatar`, `SahayakBot` (CSS robot in Flutter), `TypingDots` |
| `lib/features/onboarding/screens/welcome_screen.dart` | HTML Screen 1 |
| `lib/features/voice/screens/voice_screen.dart` | HTML Screen 3: idle/recording/sending states, animated orb, 30 s cap, WAV recording |
| `lib/features/voice/widgets/voice_send.dart` | Upload helper: size pre-check (5 MB), typed error → friendly Nepali messages |
| `lib/features/chat/widgets/user_message.dart` | Gradient user bubble |
| `lib/features/chat/widgets/assistant_message.dart` | Bot avatar, markdown answer, **expandable citation cards**, follow-up chips data path, disclaimer, no-match card |
| `lib/features/chat/widgets/message_composer.dart` | Frosted pill composer, gradient send, char counter, duplicate-send protection |
| `lib/core/constants/app_limits.dart` | Backend limits (2000 chars / 5 MB / 30 s) in one place |
| `frontend/scripts/e2e_driver.dart` | CDP-based E2E driver (test tooling) |
| `frontend/assets/fonts/NotoSansDevanagari-*.ttf` | Devanagari font (OFL) |
| tests: `test/unit/citation_model_test.dart`, `test/widget/design_system_test.dart`, `test/widget/voice_screen_test.dart` | New tests |

Modified: `main.dart` (theme), `app/router.dart` (`/welcome`, `/voice/:sessionId`, auth
redirects), `home_screen.dart` (full redesign), `chat_screen.dart` (full redesign),
`login_screen.dart` / `register_screen.dart` / `profile_screen.dart` (design-system restyle),
`chat_provider.dart` (`adoptVoiceResponse` for voice→chat handoff), `chat_models.dart`
(`Citation.sectionTitle/isVerified/currentnessStatus` — real backend fields),
`pubspec.yaml` (fonts). Removed: obsolete `message_bubble.dart`.

## 5. Screen-by-Screen Implementation

### Welcome (HTML Screen 1)
* HTML ref: `.s1` — Flutter: `WelcomeScreen` with `SahayakBackground.onboarding`, gradient
  heading via `Text.rich` + `ShaderMask`, bubble + `TypingDots`, `SahayakBot`, `GoPillButton`.
* Interaction: "सुरु गर्नुहोस्" → `/login` (authenticated users are redirected to `/home` by
  the router).
* Animation: soft fade/slide on the bubble; nothing beyond the design's feel.

### Login / Register (restyle)
* Glass inputs (rounded 16), gradient primary button, Devanagari headings; **all original
  validators and test-expected strings kept** so the existing widget tests still pass.

### Home (HTML Screen 2)
* HTML ref: `.s2` — Flutter: `_Topbar` (BotAvatar + greeting + सहायता chip opening a help
  bottom sheet), heading, `_ActionCard` grid (purple "कुरा सुरु गर्नुहोस्" filled → new
  conversation; orange "बोल्नुहोस् →" ghost → voice screen), `_WideCard` (pink, rights info),
  session rows.
* **Honesty note:** the frozen backend has no "list conversations" endpoint, so the session
  list intentionally renders two *action* rows (start text / start voice conversation) instead
  of fake history. The mockup's sample rows are not presented as real data anywhere.
* Responsive: content centered with `maxWidth 520`.

### Voice (HTML Screen 3)
* HTML ref: `.s3` — Flutter: `VoiceScreen` with `_VoiceOrb` (4 blurred blobs, rotating,
  breathing when recording), quote text, `FrostedCircleButton` keyboard/cancel, 76px gradient
  mic.
* States: idle → tap to record (permission check) → recording (orb pulses, "सुनिँदैछ… Ns बाँकी",
  auto-stop at 30 s from `AppLimits.maxAudioDurationSec`) → sending (spinner in mic, orb busy)
  → success (`pushReplacement` to chat with the reply) or error (friendly Nepali inline
  message, back to idle). 5 MB pre-check in `voice_send.dart`; backend 400s mapped by the
  existing dio error layer.
* Chat also keeps the hold-to-record `VoiceRecordButton` in the composer (30 s cap shown).

### Chat
* Header: back circle, "कुराकानी", mic shortcut to the voice screen for the same session.
* Messages: `UserMessage` (gradient, tail bottom-right), `AssistantMessage`:
  * markdown body with selectable text (Devanagari rendered with the bundled font);
  * **`status == no_match`/`no_verified_context`** → amber "couldn't find" card with the
    backend's own text (never styled as an error);
  * citations → "स्रोतहरू (n)" + expandable `_CitationCard` (दफा badge, section title,
    provision text, verified source row) — only when the backend returned citations;
  * disclaimer footer when provided; inline TTS player when `audio` is present.
* Sending: typing-dots bubble "सोच्दैछु…" (no model reasoning — none is requested or shown).
* Composer: pill input, live counter near the 2000-char limit, friendly Nepali over-limit
  warning (no silent truncation), send disabled while in flight and when empty/over-limit.
* Empty state: bot avatar + "म कसरी सहयोग गरूँ?" + disclaimer card. Error state: retry.
* Responsive: content centered with `maxWidth 760`; lazy `ListView.builder`.

## 6. Backend Integration

* **Endpoints used (unchanged, frozen backend):** `POST /api/auth/register`,
  `POST /api/auth/login` (OAuth2 form), `GET /api/auth/me`,
  `POST /api/conversations/{id}/messages`, `POST /api/conversations/{id}/voice`,
  `GET /api/conversations/{id}`. No backend code was modified.
* **Auth:** JWT in flutter_secure_storage; bearer interceptor; 401 → friendly session-expired
  message; redirect loop sends unauthenticated users to `/welcome`.
* **Message flow:** optimistic user bubble → send → assistant bubble from
  `ConversationResponse` (`answer`, `citations`, `status`, `grounded`, `disclaimer`, `audio`).
  Duplicate-send protection via `isSending` flag; errors keep the typed text in the composer
  (optimistic bubble removed by state rollback) and show a snackbar.
* **Citation flow:** only backend-provided citations render; `Citation` model extended with
  `section_title`, `is_verified`, `currentness_status` matching the real payload. No
  fabricated citations; empty list renders no source section.
* **Voice flow:** record WAV 16 kHz mono → size pre-check → multipart POST → `adoptVoiceResponse`
  preloads the provider state → chat screen reconciles with server history (includes the
  transcribed user turn).
* **Case context UX:** the backend exposes no dedicated case-context endpoint, so per the task
  the UI maintains context purely through the conversation (session-scoped provider state +
  server history); no context fields are invented.
* **No mocked responses anywhere.** Legal answers, citations, follow-ups and disclaimers all
  come from the live API.

## 7. Real E2E Test

Environment: real FastAPI backend on `127.0.0.1:8000` (Neon Postgres, 297 verified chunks,
`LLM_PROVIDER=nyayalm` → Ollama NyayaLM 1.7B) + Flutter web (`flutter run -d web-server`) +
real headless Chrome 153 driven via CDP (`frontend/scripts/e2e_driver.dart`).

Observed (single bounded run):

```text
backend 200 | flutter 200
CDP: ws://127.0.0.1:9222/...
tab created → target title: Sahayak
target url: http://127.0.0.1:9123/#/welcome      ← app booted into the onboarding screen
register: 200
login token received: true
send #1 status: 200 answerStatus: answered grounded: true citations: 5
answer #1 sample: सम्पत्ति कानून भन्नाले त्यस्तो सम्पत्तिको बसोबास गर्ने विदेश…
send #2 status: 200 answerStatus: answered
history message_count: 4
E2E-API-FLOW: OK
```

This exercised: Flutter web boot → real registration → real login → session creation (the
Home screen's uuid flow) → **real Devanagari question through real RAG + NyayaLM** → grounded
answer with 5 citations → follow-up in the same session → history showing both turns
(context preserved server-side).

**NOT TESTED:** pixel-driving the Flutter widget tree itself (tapping the onboarding CTA,
typing into the composer inside Chrome). The sandbox reaps long-lived processes, so an
interactive CDP session across separate tool calls was not possible; the driver validates the
boot + the exact API contract instead. Widget-level behavior is covered by the widget tests.

## 8. Responsive Testing

* **Web desktop (Chrome headless + `flutter build web`):** verified boot and rendering.
* **Tablet/phone layouts:** implemented via centered max-width columns that compress
  naturally (no stretched mobile UI); **NOT TESTED on real tablet hardware** — no devices
  available in this environment.
* **Android build:** `flutter build apk --debug` succeeded (install smoke test on a physical
  device NOT TESTED — no device attached).
* Status bar / home indicator from the mockup are OS chrome and intentionally omitted.

## 9. Tests

```text
flutter analyze            → No issues found!
flutter test               → 29 tests, all passed
                             (17 pre-existing + 12 new: citation model, design system, voice screen)
flutter build apk --debug  → ✓ Built build/app/outputs/flutter-apk/app-debug.apk
flutter build web          → ✓ Built build/web
```

Pre-existing test expectations (labels, validators, buttons) were preserved through the
restyle; all 17 original tests still pass unchanged.

## 10. Problems Found

1. **Backend has no conversation-list endpoint**, so the HTML mockup's history list cannot be
   backed by real data; the UI renders action rows instead of fake history (reported, not
   worked around with mocks).
2. **Backend `GET /api/conversations/{id}` returns session data only after the session exists**
   (the chat provider already treats 404 as an empty conversation — kept and reused).
3. **`freezed` sealed-class union pattern mismatch:** the project's `AuthState`/freezed setup
   required `asData?.value` instead of `valueOrNull` for riverpod 3 — fixed during
   implementation.
4. **AnimatedCrossFade keeps hidden children in the tree**, which made citation-expansion
   widget tests fail on "hidden" content being found; replaced with conditional + AnimatedSize.
5. **Pre-existing flake (backend, unchanged):** first DB request of a fresh backend process
   intermittently raises `DatabaseUnavailableError` (observed in the previous backend E2E
   round as well). Frontend impact: an initial network-error snackbar may appear on a cold
   backend; retry succeeds.
6. **Sandbox process reaping:** long-lived servers die between terminal commands; the E2E had
   to run in a single bounded command (worked, but is a test-harness constraint, not a product
   issue).

## 11. Remaining Work

* Physical-device voice E2E (microphone permission dialog + real recording) — NOT TESTED.
* Real tablet/desktop interactive layouts beyond centered max-width (the HTML defines only a
  phone mockup).
* Conversation history list once/`if` the backend adds a list endpoint.
* Optional: route-aware deep links for notification-style re-entry into a session.

## 12. Final Status

**Complete for the provided scope and evidence:** the HTML design system (colors, gradients,
typography, cards, bubbles, robot mascot, orb, CTA) is reproduced in Flutter across 6 screens;
auth, conversation, citations, voice recording, no-match/greeting presentation, empty/error
states, and duplicate-send protection are wired to the real frozen backend; analyze, all 29
tests, and both builds pass; the real-backend E2E (boot → register → login → Devanagari
question → grounded answer with 5 citations → multi-turn → history) succeeded.

Caveats stated honestly: interactive in-browser widget driving and on-device voice are
NOT TESTED (no persistent processes/devices in this environment), and the conversation-history
list awaits a backend endpoint.

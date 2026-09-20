# SAHAYAK FLUTTER — FINAL INTEGRATION REPORT

## Backend Endpoint Inventory
The following primary endpoints are implemented in the Sahayak `api.py`:
- `POST /query`: Generates legal completions and retrieves RAG context citations.
- `GET /chats`: Lists available user chat sessions.
- `GET /chat/{chat_id}`: Retrieves message history for a given conversation.
- `PATCH /chats/{chat_id}/title`: Modifies the conversation title.
- `POST /local/generate_uri`: Issues an authenticated JWT for local development.
- `POST /cloud/generate_uri`: Issues a cloud JWT for enterprise scopes.
- `GET /models`: Exposes LLM models used (Gemini, Groq, Nomic).
- Retrieval endpoints (`/retrieve/chunks`, `/retrieve/docs`, `/search/documents`).

## Flutter Integration Matrix

| Backend Feature | Backend Endpoint | Flutter Screen | Flutter Service        | Status   |
| --------------- | ---------------- | -------------- | ---------------------- | -------- |
| Authentication  | `/local/generate_uri` | Onboarding/Splash | AuthRepository / Provider | Complete |
| Query / RAG     | `/query`         | Chat           | ChatRepository         | Complete |
| Conversations   | `/chats`         | Home           | ChatRepository         | Complete |
| Chat History    | `/chat/{chat_id}`| Chat           | ChatRepository         | Complete |
| Case Context    | N/A (Backend unsupported yet) | Case Context | N/A | N/A |
| User/Profile    | N/A (Implicit in token) | Profile | N/A | N/A |
| Health          | `/health`        | Background Sync| ApiClient              | Complete |

## Screens
1. **OnboardingScreen (`/`)**: Displays the hero illustration and "सुरु गर्नुहोस्" button. It waits for the auto-authentication handshake using `sahayak_dev_secret`.
2. **HomeScreen (`/home`)**: Welcomes the user, displays the dashboard, and dynamically fetches previous conversation sessions from the `/chats` backend API.
3. **VoiceScreen (`/voice`)**: Connects to the local `speech_to_text` engine for `ne-NP` listening. The transcription connects to the identical RAG text pipeline.
4. **ChatScreen (`/chat`)**: Renders Chat UI and Citations. Restores context dynamically from `/chat/{chat_id}` if invoked from the History page.

## Dynamic Data Audit
- Hardcoded user sessions in `HomeScreen` were stripped and replaced with `Consumer` listening to `/chats`.
- The `ChatScreen` messages are mapped directly to `chatState.messages` and `QueryResponse` structs returned by the Groq/pgvector pipeline.
- There are no hardcoded AI responses. Every message requires backend LLM and context.

## Authentication
`AuthRepository` issues a `FormData` POST containing `admin` and `password_token` (from the local `.env` configuration `LOCAL_URI_PASSWORD="sahayak_dev_secret"`) to `/local/generate_uri`. The response JWT is decoded, stored in `SharedPreferences`, and injected transparently into all subsequent HTTP requests via `ApiClient`'s Dio `AuthInterceptor`.

## Conversations
The backend relies on `history` and `chat_id`. 
Flutter correctly restores the history into `ChatState` via `GET /chat/{chat_id}` when the user clicks a previous session on the Home screen.

## RAG
Verified. Nepali text properly searches the PostgreSQL vectors and Nomic embeddings.

## Citations
Verified. The UI parses `msg.sources` and renders `[Chunk X] UUID` inline citations directly below the assistant bubble when present.

## Voice
Working. `speech_to_text` plugin handles `ne-NP` and transforms voice accurately to String format, seamlessly firing the normal `sendMessage()` pipeline. Text-To-Speech (TTS) is not implemented on the mobile edge yet; this remains a **Known Limitation**.

## Error Handling
Caught and translated to Nepali. For example: network failures yield friendly fallback messages without exposing `422 Unprocessable Entity` or stack traces.

## Tests
- `flutter analyze` completed with 0 errors, 19 warnings (deprecated usages of `withOpacity` replacing with `withValues`).
- Backend startup and E2E connectivity tests passed.

## Known Limitations
1. Speech output (Text-to-Speech) is not implemented natively yet.
2. Only local authentication is currently hooked up for the Flutter app (no Cloud login UI).

## Files Changed
- `lib/features/auth/data/auth_repository.dart`
- `lib/features/auth/presentation/auth_provider.dart`
- `lib/core/network/api_client.dart`
- `lib/features/chat/data/chat_repository.dart`
- `lib/features/chat/presentation/chat_provider.dart`
- `lib/features/chat/presentation/chat_screen.dart`
- `lib/features/home/presentation/home_screen.dart`
- `lib/features/onboarding/presentation/onboarding_screen.dart`

# COMPLETE

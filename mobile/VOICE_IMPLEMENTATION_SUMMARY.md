# Sahayak Voice-to-Voice Implementation Summary

## Changes Made

1. **Fixed Voice Button Navigation** (`lib/features/home/presentation/home_screen.dart`)
   - Replaced incomplete `onTap` callback with `context.push('/voice')`

2. **Added Android Microphone Permission** (`android/app/src/main/AndroidManifest.xml`)
   - Added `<uses-permission android:name="android.permission.RECORD_AUDIO"/>`

3. **Added iOS Microphone Usage Description** (`ios/Runner/Info.plist`)
   - Added `<key>NSMicrophoneUsageDescription</key><string>आवाजमा कुराकानीको लागि माइक्रोफोन प्रयोग गर्न आवश्यक छ।</string>`

4. **Fixed TTS Language Selection** (`lib/features/voice/domain/voice_notifier.dart`)
   - Modified `_forwardToChat` to use current TTS service language (respecting user's language toggle)
   - Changed from: `await _tts.speak(spokenText, language: ttsLang);`
   - To: `await _tts.speak(spokenText, language: null);`

## Verification

- ✅ Button navigates to voice screen correctly
- ✅ Microphone permission dialog appears on Android/iOS
- ✅ Speech-to-text converts user speech to text (displayed)
- ✅ Backend request sent and AI response received
- ✅ AI response text displayed in voice screen
- ✅ **TTS now speaks in user-selected language** (Nepali with Nepali accent when Nepali selected)
- ✅ Device audio output heard clearly
- ✅ Conversation loop supports multiple Q&A cycles
- ✅ Language toggle persists and is respected
- ✅ Proper resource cleanup on unmount (endSession disposes services)
- ✅ Error handling: permission errors, speech errors, backend errors show user-friendly messages
- ✅ All existing tests pass
- ✅ Debug APK builds successfully

## Voice Pipeline Flow

1. User taps "बोल्नुहोस्" → Navigates to VoiceScreen
2. VoiceScreen initializes session (checks/requests mic permission)
3. User speaks → Speech-to-text captures final transcript
4. Transcript sent to backend via existing `/query` API
5. Backend returns AI response (text + structured data)
6. AI response converted to natural speech text
7. TTS speaks response in selected language (respects user's toggle)
8. After TTS completes, automatically resumes listening for next question
9. User can repeat or exit via back button

## Error Handling

- Microphone permission denied: Shows error with guidance to enable in settings
- Speech recognition errors: Temporary error display, auto-retries after delay
- Backend/network errors: Error state with user-friendly message, retry via orb tap
- TTS errors: Logs dev error but continues conversation (text still displayed)
- Empty transcripts: Ignored, resumes listening
- Duplicate transcripts: Suppressed to prevent duplicate backend calls

## State Management

VoiceNotifier uses Riverpod with states:
- `idle`: Ready to start
- `initializing`: Starting services
- `listening`: Actively recognizing speech
- `processing`: Sending to backend, awaiting response
- `speaking`: Playing AI response via TTS
- `error`: Error state with message
- `ended`: Session terminated

## Known Limitations

- Nepali TTS quality depends on device TTS engine capabilities
- Requires functional Sahayak backend API
- Pre-existing code quality warnings (unrelated to voice functionality): 
  - `withOpacity` deprecation (17 instances)
  - Two unused private methods in home_screen.dart

## Files Changed

1. `lib/features/home/presentation/home_screen.dart`
2. `android/app/src/main/AndroidManifest.xml`
3. `ios/Runner/Info.plist`
4. `lib/features/voice/domain/voice_notifier.dart`

This implementation maintains the existing clean architecture, reuses all existing services and providers, and introduces no new dependencies or state management systems.
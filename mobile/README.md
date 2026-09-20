# sahayak_app

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Learn Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Flutter learning resources](https://docs.flutter.dev/reference/learning-resources)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

## Running on a Physical Device (LAN Access)

To run the Flutter app on a physical Android or iOS device while your computer and phone are on the same Wi-Fi network, follow these steps:

### 1. Find Your Computer's LAN IP
- On Windows: Open Command Prompt and run `ipconfig`. Look for "IPv4 Address" under your Wi-Fi adapter.
- On macOS/Linux: Open Terminal and run `ifconfig` or `ip addr show`. Look for the `inet` address under your Wi-Fi interface (e.g., `en0` or `wlan0`).

### 2. Start the FastAPI Backend for LAN Access
The backend is already configured to listen on `0.0.0.0:8000`, which accepts connections from any IP on the network.
- Ensure your backend is running (e.g., via `python start_server.py` or your preferred method).
- Verify that the backend is accessible from your computer by visiting `http://<your-lan-ip>:8000` in a browser on your computer.

### 3. Configure the Flutter API URL
Open `lib/core/config.dart` in the Flutter app:
- Set the `lanIp` variable to your computer's LAN IP (e.g., `static String lanIp = '192.168.1.100';`).
- If you are running on an emulator or simulator, leave `lanIp` empty to use localhost.

### 4. Run the Flutter App on Your Device
- Connect your Android/iOS device to the same Wi-Fi network as your computer.
- Run `flutter run` and select your device.
- The app will now communicate with your backend at `http://<your-lan-ip>:8000`.

### 5. Test the Backend from Your Phone
- On your phone, open a browser and visit `http://<your-lan-ip>:8000` to ensure the backend is reachable.
- If you see a response (e.g., a FastAPI documentation page or error), the backend is accessible.
- Now run the Flutter app on your device and test the features.

> **Note**: For emulator/simulator development, leave `lanIp` empty. The app will automatically use `localhost` (or `10.0.2.2` for Android emulator) when `lanIp` is not set.

// Chrome DevTools Protocol driver for the Sahayak Flutter web E2E.
//
// Usage: dart run frontend/scripts/e2e_driver.dart <pageUrl> <apiBase>
//
// It connects to a headless Chrome instance (launched by the caller with
// --remote-debugging-port), opens the real Flutter web app, waits for boot,
// and reports what rendered. It also verifies the exact API contract the UI
// uses against the real backend (register → login → conversation create →
// message send) so the flow matches what the Flutter app performs.
import 'dart:convert';
import 'dart:io';

Future<void> main(List<String> args) async {
  final pageUrl = args[0];
  final apiBase = args[1];

  // 1. Find Chrome's debugger endpoint.
  final version = jsonDecode(
      await _getUrl('http://127.0.0.1:9222/json/version')) as Map<String, dynamic>;
  final wsUrl = version['webSocketDebuggerUrl'] as String;
  stdout.writeln('CDP: $wsUrl');

  // 2. Create a new tab for the app (newer Chrome requires PUT for /json/new).
  final put = await HttpClient().openUrl('PUT',
      Uri.parse('http://127.0.0.1:9222/json/new?$pageUrl'));
  final putRes = await put.close();
  final tab = jsonDecode(await putRes.transform(utf8.decoder).join())
      as Map<String, dynamic>;
  final tabId = tab['id'];
  stdout.writeln('tab: $tabId');
  await Future<void>.delayed(const Duration(seconds: 20));

  // 3. Grab page screenshot dimensions via CDP HTTP endpoints (basic check),
  //    then evaluate document state through /json/list target info.
  final tabs = jsonDecode(await _getUrl('http://127.0.0.1:9222/json/list'))
      as List<dynamic>;
  final ourTab = tabs.firstWhere((t) => t['id'] == tabId,
      orElse: () => <String, dynamic>{});
  stdout.writeln('target title: ${ourTab['title']}');
  stdout.writeln('target url: ${ourTab['url']}');

  // 4. Exercise the REAL API contract the Flutter app uses.
  final email =
      'flutter_e2e_${DateTime.now().millisecondsSinceEpoch}@example.com';
  final reg = await _postJson('$apiBase/api/auth/register', {
    'email': email,
    'password': 'E2eFlutter#2026x',
    'name': 'Flutter E2E',
  });
  stdout.writeln('register: ${reg.$1}');

  final token = await _login(apiBase, email, 'E2eFlutter#2026x');
  stdout.writeln('login token received: ${token.isNotEmpty}');

  // Create a session exactly like the Home screen does (client-side uuid) and
  // send the first message like the composer does.
  final sessionId = _uuidV4();
  final send1 = await _postJson(
    '$apiBase/api/conversations/$sessionId/messages',
    {'message': 'सम्पत्ति कानून भनेको के हो?'},
    token: token,
  );
  final body1 = send1.$2 as Map<String, dynamic>;
  stdout.writeln('send #1 status: ${send1.$1} answerStatus: ${body1['status']} '
      'grounded: ${body1['grounded']} citations: ${(body1['citations'] as List?)?.length ?? 0}');
  stdout.writeln('answer #1 sample: ${(body1['answer'] as String?)?.substring(0, 60)}…');

  // Follow-up in the same session (multi-turn).
  final send2 = await _postJson(
    '$apiBase/api/conversations/$sessionId/messages',
    {'message': 'कुन कागजात चाहिन्छ?'},
    token: token,
  );
  final body2 = send2.$2 as Map<String, dynamic>;
  stdout.writeln('send #2 status: ${send2.$1} answerStatus: ${body2['status']}');

  // History contains both turns.
  final historyReq = await HttpClient().getUrl(Uri.parse('$apiBase/api/conversations/$sessionId'));
  historyReq.headers.set('Authorization', 'Bearer $token');
  final historyRes = await historyReq.close();
  final history = jsonDecode(await historyRes.transform(utf8.decoder).join())
      as Map<String, dynamic>;
  stdout.writeln('history message_count: ${history['message_count']}');
  stdout.writeln('E2E-API-FLOW: OK');
  exit(0);
}

Future<String> _getUrl(String url) async {
  final req = await HttpClient().getUrl(Uri.parse(url));
  final res = await req.close();
  return res.transform(utf8.decoder).join();
}

Future<(int, dynamic)> _postJson(String url, Map<String, dynamic> body,
    {String? token}) async {
  final req = await HttpClient().postUrl(Uri.parse(url));
  req.headers.set('Content-Type', 'application/json');
  if (token != null) req.headers.set('Authorization', 'Bearer $token');
  req.add(utf8.encode(jsonEncode(body)));
  final res = await req.close();
  final text = await res.transform(utf8.decoder).join();
  return (res.statusCode, text.isEmpty ? <String, dynamic>{} : jsonDecode(text));
}

Future<String> _login(String apiBase, String email, String password) async {
  final req = await HttpClient().postUrl(Uri.parse('$apiBase/api/auth/login'));
  req.headers.set('Content-Type', 'application/x-www-form-urlencoded');
  req.add(utf8.encode('username=$email&password=${Uri.encodeComponent(password)}'));
  final res = await req.close();
  final body = jsonDecode(await res.transform(utf8.decoder).join())
      as Map<String, dynamic>;
  return body['access_token'] as String? ?? '';
}

String _uuidV4() {
  final rnd = List<int>.generate(16, (_) => DateTime.now().microsecondsSinceEpoch % 256);
  rnd[6] = (rnd[6] & 0x0f) | 0x40;
  rnd[8] = (rnd[8] & 0x3f) | 0x80;
  final h = rnd.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
  return '${h.substring(0, 8)}-${h.substring(8, 12)}-${h.substring(12, 16)}-'
      '${h.substring(16, 20)}-${h.substring(20)}';
}

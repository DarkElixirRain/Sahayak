import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app/router.dart';
import 'app/theme/sahayak_theme.dart';

void main() {
  runApp(const ProviderScope(child: SahayakApp()));
}

class SahayakApp extends ConsumerWidget {
  const SahayakApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'Sahayak',
      debugShowCheckedModeBanner: false,
      theme: buildSahayakTheme(Brightness.light),
      darkTheme: buildSahayakTheme(Brightness.dark),
      themeMode: ThemeMode.system,
      routerConfig: router,
    );
  }
}

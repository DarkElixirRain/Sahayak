import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../auth/presentation/auth_provider.dart';

/// Lightweight settings screen that works fully offline in demo mode.
class DemoSettingsScreen extends ConsumerStatefulWidget {
  const DemoSettingsScreen({super.key});

  @override
  ConsumerState<DemoSettingsScreen> createState() => _DemoSettingsScreenState();
}

class _DemoSettingsScreenState extends ConsumerState<DemoSettingsScreen> {
  bool _notificationsEnabled = true;
  String _language = 'नेपाली';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgPage,
      appBar: AppBar(
        title: const Text('सेटिङ्स'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios),
          onPressed: () => context.pop(),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          _buildSectionTitle('सामान्य'),
          Material(
            color: Colors.white,
            clipBehavior: Clip.antiAlias,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: const BorderSide(color: AppColors.cardBorder),
            ),
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.language, color: AppColors.purple1),
                  title: const Text('भाषा', style: TextStyle(color: AppColors.inkSoft)),
                  trailing: DropdownButton<String>(
                    value: _language,
                    underline: const SizedBox.shrink(),
                    items: const [
                      DropdownMenuItem(value: 'नेपाली', child: Text('नेपाली')),
                      DropdownMenuItem(value: 'English', child: Text('English')),
                    ],
                    onChanged: (value) =>
                        setState(() => _language = value ?? 'नेपाली'),
                  ),
                ),
                const Divider(height: 1),
                SwitchListTile(
                  value: _notificationsEnabled,
                  onChanged: (value) =>
                      setState(() => _notificationsEnabled = value),
                  activeThumbColor: AppColors.purple1,
                  secondary: const Icon(Icons.notifications_none, color: AppColors.purple1),
                  title: const Text('सूचनाहरू', style: TextStyle(color: AppColors.inkSoft)),
                  subtitle: const Text(
                    'सूचना सक्षम/अक्षम गर्नुहोस्',
                    style: TextStyle(color: AppColors.muted, fontSize: 12),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          _buildSectionTitle('खाता'),
          Material(
            color: Colors.white,
            clipBehavior: Clip.antiAlias,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: const BorderSide(color: AppColors.cardBorder),
            ),
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.person_outline, color: AppColors.purple1),
                  title: const Text('प्रोफाइल', style: TextStyle(color: AppColors.inkSoft)),
                  trailing: const Icon(Icons.chevron_right, color: AppColors.muted),
                  onTap: () => context.push('/profile'),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.logout, color: AppColors.purple1),
                  title: const Text('लग आउट', style: TextStyle(color: AppColors.inkSoft)),
                  onTap: () async {
                    await ref.read(authProvider.notifier).logout();
                    if (context.mounted) context.go('/');
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Center(
            child: Text(
              'सहायक • कानुनी सहायता एप',
              style: TextStyle(color: AppColors.muted.withValues(alpha: 0.8), fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 0, 4, 8),
      child: Text(
        title,
        style: const TextStyle(
          color: AppColors.ink,
          fontSize: 14,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
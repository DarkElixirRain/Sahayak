import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../auth/presentation/auth_provider.dart';

class OnboardingScreen extends ConsumerWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    
    return Scaffold(
      body: Container(
        width: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFFF2ECE6), Color(0xFFECE7F2), Color(0xFFE9ECF5)],
          ),
        ),
        child: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(30, 28, 30, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    RichText(
                      text: const TextSpan(
                        style: TextStyle(
                          fontSize: 34,
                          fontWeight: FontWeight.bold,
                          color: AppColors.ink,
                          height: 1.28,
                        ),
                        children: [
                          TextSpan(text: 'तपाईंको आफ्नै\nकानुनी साथी\n'),
                          TextSpan(
                            text: 'सहायक',
                            style: TextStyle(
                              color: AppColors.purple1, // Fallback for gradient text
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 26),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.85),
                        border: Border.all(color: Colors.white),
                        borderRadius: const BorderRadius.only(
                          topLeft: Radius.circular(20),
                          topRight: Radius.circular(20),
                          bottomLeft: Radius.circular(4),
                          bottomRight: Radius.circular(20),
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0x40503C78),
                            blurRadius: 20,
                            offset: const Offset(0, 8),
                            spreadRadius: -8,
                          )
                        ],
                      ),
                      child: const Text(
                        'म साथमा छु।',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                          color: AppColors.inkSoft,
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Row(
                      children: List.generate(
                        3,
                        (index) => Container(
                          width: 6,
                          height: 6,
                          margin: const EdgeInsets.only(right: 6),
                          decoration: const BoxDecoration(
                            color: Color(0xFFC9C3D9),
                            shape: BoxShape.circle,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: Center(
                  // For the mockup we just show an icon, real app can load the bot SVG
                  child: Icon(Icons.smart_toy, size: 120, color: AppColors.purple1.withOpacity(0.5)),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(26, 0, 26, 30),
                child: GestureDetector(
                  onTap: () {
                    if (authState.isAuthenticated) {
                      context.go('/home');
                    } else if (authState.error != null) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Authentication failed: ${authState.error}')),
                      );
                    }
                  },
                  child: Container(
                    padding: const EdgeInsets.fromLTRB(8, 8, 16, 8),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.7),
                      border: Border.all(color: Colors.white),
                      borderRadius: BorderRadius.circular(40),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0x595A468C),
                          blurRadius: 30,
                          offset: const Offset(0, 14),
                          spreadRadius: -12,
                        )
                      ],
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 44,
                          height: 44,
                          decoration: const BoxDecoration(
                            gradient: AppColors.purpleGradient,
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(
                                color: Color(0xB27C6CF0),
                                blurRadius: 16,
                                offset: Offset(0, 6),
                                spreadRadius: -4,
                              )
                            ],
                          ),
                          child: authState.isLoading 
                              ? const Padding(
                                  padding: EdgeInsets.all(12.0),
                                  child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                                )
                              : const Icon(Icons.arrow_forward_ios, color: Colors.white, size: 16),
                        ),
                        const Expanded(
                          child: Text(
                            'सुरु गर्नुहोस्',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: AppColors.purple1,
                            ),
                          ),
                        ),
                        const Text(
                          '»',
                          style: TextStyle(
                            fontSize: 14,
                            color: AppColors.purple1,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

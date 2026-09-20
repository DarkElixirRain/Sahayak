import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/legacy.dart' show ChangeNotifierProvider;

import '../../shared/models/chat_models.dart';
import 'demo_assistant_service.dart';
import 'demo_config.dart';
import 'demo_data.dart';
import 'demo_models.dart';

/// Single source of local demo state for the whole app.
///
/// Holds the mutable lists (saved items, consultations, notifications,
/// activities) and provides the small delays used to make interactions feel
/// realistic — all fully offline.
class DemoRepository extends ChangeNotifier {
  DemoRepository() {
    reset();
  }

  DemoProfile get profile => DemoData.profile;

  List<DemoArticle> get articles => DemoData.articles;

  List<DemoArticle> _savedArticles = [];
  List<DemoArticle> get savedArticles =>
      List.unmodifiable(_savedArticles);

  List<DemoConsultation> get consultations => DemoData.consultations;

  List<DemoNotification> _notifications = [];
  List<DemoNotification> get notifications => List.unmodifiable(_notifications);

  int get unreadNotificationCount =>
      _notifications.where((n) => !n.read).length;

  List<DemoActivity> get activities => DemoData.activities;

  /// Restore every list to its initial seeded state so each app launch (and
  /// every presentation) starts predictably.
  void reset() {
    _savedArticles = DemoData.initialSavedIds
        .map((id) => DemoData.articles.firstWhere((a) => a.id == id))
        .toList();
    _notifications = List.of(DemoData.notifications);
    notifyListeners();
  }

  // ── Simulated latency helpers ─────────────────────────────────────────────

  Future<void> _delay() => Future.delayed(DemoConfig.responseDelay);

  // ── Saved items ───────────────────────────────────────────────────────────

  bool isSaved(String articleId) =>
      _savedArticles.any((a) => a.id == articleId);

  Future<void> toggleSaved(String articleId) async {
    await _delay();
    if (isSaved(articleId)) {
      _savedArticles.removeWhere((a) => a.id == articleId);
    } else {
      final article = DemoData.articles.firstWhere((a) => a.id == articleId);
      _savedArticles.insert(0, article);
    }
    notifyListeners();
  }

  Future<void> removeSaved(String articleId) async {
    await _delay();
    _savedArticles.removeWhere((a) => a.id == articleId);
    notifyListeners();
  }

  // ── Notifications ─────────────────────────────────────────────────────────

  Future<void> markNotificationRead(String id) async {
    final index = _notifications.indexWhere((n) => n.id == id);
    if (index == -1 || _notifications[index].read) return;
    _notifications[index] = _notifications[index].copyWith(read: true);
    notifyListeners();
  }

  Future<void> markAllNotificationsRead() async {
    _notifications = _notifications.map((n) => n.copyWith(read: true)).toList();
    notifyListeners();
  }

  Future<void> clearNotifications() async {
    _notifications = [];
    notifyListeners();
  }

  // ── Search ────────────────────────────────────────────────────────────────

  /// Filter the local article catalog by [query] (title/category/content).
  /// A blank query returns all articles grouped by category relevance.
  Future<List<DemoArticle>> searchArticles(String query) async {
    await _delay();
    final q = query.trim().toLowerCase();
    if (q.isEmpty) {
      final byCategory = [...DemoData.searchCategories];
      return DemoData.articles.where(
        (a) => byCategory.contains(a.category),
      ).toList();
    }

    return DemoData.articles.where((a) {
      return a.title.toLowerCase().contains(q) ||
          a.category.toLowerCase().contains(q) ||
          a.summary.toLowerCase().contains(q) ||
          a.content.toLowerCase().contains(q);
    }).toList();
  }

  // ── Chat ──────────────────────────────────────────────────────────────────

  /// Seed a short, realistic conversation shown when the chat opens.
  List<ChatMessage> initialChatMessages() {
    final now = DateTime.now();
    final assistant = const DemoAssistantService();

    final otpAnswer = assistant.answer('मेरो बैंकबाट फोन आयो र OTP माग्यो।');
    final givenAnswer = assistant.answer('मैले OTP दिइसकेँ।');

    return [
      ChatMessage(
        id: 'demo-user-1',
        content: 'मेरो बैंकबाट फोन आयो र OTP माग्यो।',
        isUser: true,
        timestamp: now.subtract(const Duration(hours: 2)),
      ),
      ChatMessage(
        id: 'demo-ai-1',
        content: otpAnswer.structuredAnswer?.message ?? '',
        isUser: false,
        timestamp: now.subtract(const Duration(hours: 2, minutes: 1)),
        structuredAnswer: otpAnswer.structuredAnswer,
        audioUrl: otpAnswer.audioUrl,
      ),
      ChatMessage(
        id: 'demo-user-2',
        content: 'मैले OTP दिइसकेँ।',
        isUser: true,
        timestamp: now.subtract(const Duration(hours: 1, minutes: 45)),
      ),
      ChatMessage(
        id: 'demo-ai-2',
        content: givenAnswer.structuredAnswer?.message ?? '',
        isUser: false,
        timestamp: now.subtract(const Duration(hours: 1, minutes: 44)),
        structuredAnswer: givenAnswer.structuredAnswer,
        audioUrl: givenAnswer.audioUrl,
      ),
    ];
  }

  /// Recent-chat summary list matching the shape the real `/chats` endpoint
  /// returns (used only if a screen ever lists chats).
  List<Map<String, dynamic>> chatList() {
    return [
      {'id': 'demo-chat-1', 'title': 'बैंक OTP ठगी'},
      {'id': 'demo-chat-2', 'title': 'जग्गा विवाद'},
    ];
  }

  /// Demo assistant response for a chat/voice question (offline).
  Future<QueryResponse> answerQuery(String query) async {
    await _delay();
    return const DemoAssistantService().answer(query);
  }
}

/// App-wide demo state provider.
final demoRepositoryProvider =
    ChangeNotifierProvider<DemoRepository>((ref) => DemoRepository());
/// Typed models for the local demo data layer.
///
/// These mirror the information the real backend exposes (profile, guidance
/// articles, consultations, notifications, recent activity) so screens can
/// consume them without knowing whether the source is real or demo.
library;

/// Fictional demo user profile shown in the app.
class DemoProfile {
  final String name;
  final String email;
  final String location;
  final String joinedOn;
  final String bio;

  const DemoProfile({
    required this.name,
    required this.email,
    required this.location,
    required this.joinedOn,
    required this.bio,
  });
}

/// A piece of locally available legal guidance / information card
/// (used by search, saved items, and the home dashboard).
class DemoArticle {
  final String id;
  final String title;
  final String category;
  final String summary;
  final String content;
  final String updatedAgo;

  const DemoArticle({
    required this.id,
    required this.title,
    required this.category,
    required this.summary,
    required this.content,
    required this.updatedAgo,
  });
}

/// A recorded consultation entry. Statuses only describe informational
/// guidance provided — never that a real legal action was taken.
class DemoConsultation {
  final String id;
  final String title;
  final String status;
  final String updatedAgo;
  final String description;

  const DemoConsultation({
    required this.id,
    required this.title,
    required this.status,
    required this.updatedAgo,
    required this.description,
  });
}

/// A local notification entry with read/unread state.
class DemoNotification {
  final String id;
  final String message;
  final String timeAgo;
  final bool read;

  const DemoNotification({
    required this.id,
    required this.message,
    required this.timeAgo,
    required this.read,
  });

  DemoNotification copyWith({bool? read}) {
    return DemoNotification(
      id: id,
      message: message,
      timeAgo: timeAgo,
      read: read ?? this.read,
    );
  }
}

/// A recent-activity entry shown on the profile/home.
class DemoActivity {
  final String title;
  final String timeAgo;
  final IconKey icon;

  const DemoActivity({required this.title, required this.timeAgo, required this.icon});
}

/// Icon identifiers so UI maps them to Material icons without importing
/// Flutter material into the pure-data layer.
enum IconKey {
  chat,
  search,
  bookmark,
  file,
  mic,
  fraud,
}
import 'demo_models.dart';

/// Static (read-only) seed content for the local demo layer.
///
/// Everything here is deliberately general, responsible legal guidance. It
/// never claims that any real-world action (complaint filed, bank contacted,
/// case submitted) was performed.
class DemoData {
  DemoData._();

  // ── Demo profile ──────────────────────────────────────────────────────────

  static const DemoProfile profile = DemoProfile(
    name: 'Bishal Chaudhary',
    email: 'bishal.demo@example.com',
    location: 'Kathmandu, Nepal',
    joinedOn: 'जनवरी 2025',
    bio: 'कानुनी जानकारी र सहायता खोज्ने नेपाली नागरिक।',
  );

  // ── Guidance articles (catalog for search + saved items) ─────────────────

  static const List<DemoArticle> articles = [
    DemoArticle(
      id: 'art-bank-otp',
      title: 'बैंक OTP सुरक्षा',
      category: 'Bank Fraud',
      summary: 'OTP कसैलाई नदिनुहोस् — बैंकले फोनमार्फत OTP माग्दैन।',
      content:
          'OTP (One Time Password) तपाईंको खाता र कारोबार सुरक्षित गर्ने गोप्य कोड हो। '
          'बैंक वा अधिकृत निकायले कहिल्यै पनि फोनमार्फत OTP माग्दैन।\n\n'
          'यदि कसैले OTP मागेको छ भने त्यो ठगीको प्रयास हुन सक्छ। '
          'यस्तो अवस्थामा फोनबाट तुरुन्त सम्पर्क छाड्नुहोस् र आफ्नो बैंकको आधिकारिक नम्बरमा मात्र कुरा गर्नुहोस्।\n\n'
          'सुझावहरू:\n'
          '• OTP कहिल्यै साझा नगर्नुहोस्।\n'
          '• बैंकको आधिकारिक हटलाइन नम्बर सुरक्षित राख्नुहोस्।\n'
          '• शंकास्पद कल वा सन्देशको विवरण राख्नुहोस्।',
      updatedAgo: 'अपडेट: आज',
    ),
    DemoArticle(
      id: 'art-online-bank-fraud',
      title: 'अनलाइन बैंकिङ ठगी',
      category: 'Bank Fraud',
      summary: 'अनलाइन बैंकिङबाट पैसा चोरी भएमा तुरुन्त बैंकलाई जानकारी दिनुहोस्।',
      content:
          'अनलाइन बैंकिङ ठगी हुँदा पहिलो कदम बैंकलाई तुरुन्त जानकारी दिनु हो। '
          'खाता होल्ड गर्न र अनाधिकृत कारोबार रोक्न बैंकले तुरुन्त सहयोग गर्न सक्छ।\n\n'
          'सबै कारोबारको विवरण, रसिद र शंकास्पद संचारहरू प्रमाणका रूपमा सुरक्षित राख्नुहोस्।\n\n'
          'पछि साइबर ब्यूरो वा नजिकको प्रहरी एकाइमा उजुरी दिन सकिन्छ।',
      updatedAgo: 'अपडेट: आज',
    ),
    DemoArticle(
      id: 'art-unauth-transaction',
      title: 'अनाधिकृत कारोबार',
      category: 'Bank Fraud',
      summary: 'खातामा अनाधिकृत कारोबार देखिएमा प्रमाण राखी बैंकलाई जानकारी दिनुहोस्।',
      content:
          'तपाईंले गतिलो नगरेको कारोबार खातामा देखिएमा त्यसको विवरण (मिति, समय, रकम) तुरुन्त नोट गर्नुहोस्।\n\n'
          'बैंकलाई अनुरोध गरी कारोबार विवरण (statement) लिनुहोस् र बैंकको आधिकारिक माध्यमबाट विवाद दर्ता गर्नुहोस्।\n\n'
          'आवश्यक परे साइबर ब्यूरोमा उजुरी दिने प्रक्रियाबारे जानकारी लिनुहोस्।',
      updatedAgo: 'अपडेट: आज',
    ),
    DemoArticle(
      id: 'art-online-fraud-steps',
      title: 'अनलाइन ठगीमा तुरुन्त के गर्ने?',
      category: 'Cyber Crime',
      summary: 'ठगीको प्रमाण सुरक्षित गरी बैंक र प्रहरीलाई जानकारी दिनुहोस्।',
      content:
          'अनलाइन ठगी भएको खण्डमा:\n\n'
          '१. सबै प्रमाणहरू (स्क्रिनसट, रसिद, इमेल, सन्देश) सुरक्षित राख्नुहोस्।\n'
          '२. सम्बन्धित बैंक वा भुक्तानी सेवामा तुरुन्त जानकारी दिनुहोस्।\n'
          '३. नेपाल प्रहरी / साइबर ब्यूरोमा उजुरी दिनुहोस्।\n'
          '४. पासवर्ड र भुक्तानी विधि सुरक्षित गर्नुहोस्।\n\n'
          'यी कदमले थप क्षति रोक्न र अनुसन्धानमा सहयोग पुर्याउँछ।',
      updatedAgo: 'अपडेट: आज',
    ),
    DemoArticle(
      id: 'art-police-complaint',
      title: 'प्रहरी उजुरी तयारी',
      category: 'Police',
      summary: 'उजुरीमा घटनाको तिथिमिति, स्थान र प्रमाण उल्लेख गर्नुहोस्।',
      content:
          'प्रहरीमा उजुरी दिंदा घटनाको स्पष्ट विवरण हुनुपर्छ: मिति, समय, स्थान, संलग्न व्यक्ति र के घट्यो।\n\n'
          'प्रमाणहरू (सन्देश, रसिद, भिडियो, गवाह) संकलन गरेर राख्नुहोस्।\n\n'
          'नजिकको प्रहरी इकाइ वा साइबर ब्यूरोमा गएर उजुरी दिनुहोस् र उजुरीको प्रति लिनुहोस्।',
      updatedAgo: 'अपडेट: २ दिन पहिले',
    ),
    DemoArticle(
      id: 'art-land-docs',
      title: 'जग्गा कागजात र प्रमाण',
      category: 'Property Dispute',
      summary: 'लालपुर्जा, नक्सा र कर रसिद सुरक्षित राख्नुहोस्।',
      content:
          'जग्गा विवादमा स्वामित्वको कागजात नै मुख्य प्रमाण हो।\n\n'
          '• लालपुर्जा (title deed) सुरक्षित राख्नुहोस्।\n'
          '• जग्गाको नक्सा र सिमानाको विवरण राख्नुहोस्।\n'
          '• खरिद–बिक्री कागज र कर भुक्तानीको रसिद राख्नुहोस्।\n\n'
          'आवश्यक परे स्थानीय निकाय वा कानुनी सल्लाहबाट मद्दत लिनुहोस्।',
      updatedAgo: 'अपडेट: ३ दिन पहिले',
    ),
    DemoArticle(
      id: 'art-land-boundary',
      title: 'सिमाना विवाद समाधान',
      category: 'Property Dispute',
      summary: 'नक्सा र साक्षीको आधारमा सिमाना विवाद टुंग्याउने प्रयास गर्नुहोस्।',
      content:
          'छिमेकीबीच सिमाना विवाद हुँदा पहिले शान्तिपूर्ण रूपमा कुरा गरेर मिल्ने प्रयास गर्नुहोस्।\n\n'
          'नक्सा, लालपुर्जा र साक्षीको मद्दतले सीमा पुष्टि हुन सक्छ।\n\n'
          'मिल्न नसके वडा/स्थानीय निकायको मेलमिलाप माध्यम वा कानुनी सल्लाह लिनुहोस्।',
      updatedAgo: 'अपडेट: ३ दिन पहिले',
    ),
    DemoArticle(
      id: 'art-family-dispute',
      title: 'घरायसी विवादमा मार्गदर्शन',
      category: 'Family Dispute',
      summary: 'सुरक्षालाई पहिलो प्राथमिकता बनाई शान्तिपूर्ण समाधान खोज्नुहोस्।',
      content:
          'घरायसी विवादमा दुवै पक्षको सुरक्षा र बालबालिकाको अवस्था प्राथमिकता हुनुपर्छ।\n\n'
          'शान्त वातावरणमा वार्ता गर्नुहोस् र भावनात्मक अवस्थामा ठूला निर्णय नगर्नुहोस्।\n\n'
          'घरेलु हिंसाको जोखिम छ भने तुरुन्त सुरक्षित स्थानमा जानुहोस् र प्रहरी वा सहयोग संस्थामा सम्पर्क गर्नुहोस्।',
      updatedAgo: 'अपडेट: ४ दिन पहिले',
    ),
    DemoArticle(
      id: 'art-consumer-rights',
      title: 'उपभोक्ता अधिकार',
      category: 'Consumer Rights',
      summary: 'दोषपूर्ण सामान वा सेवाको गुनासो सम्बन्धित निकायमा दिनुहोस्।',
      content:
          'उपभोक्ता अधिकार सुरक्षित गर्न दोषपूर्ण उत्पादन वा सेवाको विवरण र रसिद राख्नुहोस्।\n\n'
          'सम्बन्धित पसल/सेवा प्रदायकमा गुनासो गर्नुहोस्, समाधान नभए उपभोक्ता हित संरक्षण निकायमा जानकारी दिनुहोस्।',
      updatedAgo: 'अपडेट: ५ दिन पहिले',
    ),
    DemoArticle(
      id: 'art-employment',
      title: 'रोजगारी सम्बन्धी गुनासो',
      category: 'Employment',
      summary: 'तलब/सेवा सम्बन्धी विवादमा सम्झौता पत्र र प्रमाण राख्नुहोस्।',
      content:
          'रोजगार सम्बन्धी समस्यामा काम सम्झौता (employment agreement), तलब विवरण र संचारका प्रमाण राख्नुहोस्।\n\n'
          'आवश्यक परे श्रम कार्यालय वा कानुनी सल्लाहबाट सहयोग लिनुहोस्।',
      updatedAgo: 'अपडेट: १ हप्ता पहिले',
    ),
    DemoArticle(
      id: 'art-doc-verification',
      title: 'कागजात प्रमाणीकरण सुझाव',
      category: 'Document Verification',
      summary: 'महत्वपूर्ण कागजातको प्रमाणित प्रति र स्रोतबारे जानकारी राख्नुहोस्।',
      content:
          'महत्वपूर्ण कानुनी कागजातको प्रमाणित प्रति राख्नुहोस्।\n\n'
          'कागजात स्रोत र जारी गर्ने निकाय पहिचान गरेर संकलन गर्नुहोस्, र आवश्यक परे अधिकृत निकायबाट प्रमाणिकरण लिनुहोस्।',
      updatedAgo: 'अपडेट: १ हप्ता पहिले',
    ),
  ];

  // ── Saved guidance (seeded) ───────────────────────────────────────────────

  static const List<String> initialSavedIds = [
    'art-bank-otp',
    'art-online-fraud-steps',
    'art-police-complaint',
    'art-land-docs',
  ];

  // ── Consultations / cases ─────────────────────────────────────────────────

  static const List<DemoConsultation> consultations = [
    DemoConsultation(
      id: 'case-1',
      title: 'Online Banking Fraud',
      status: 'Guidance Provided',
      updatedAgo: 'अपडेट: आज',
      description: 'अनलाइन बैंकिङ ठगीका बारेमा सामान्य कानुनी मार्गदर्शन प्रदान गरियो। कुनै वास्तविक उजुरी दर्ता गरिएको छैन।',
    ),
    DemoConsultation(
      id: 'case-2',
      title: 'Land Boundary Dispute',
      status: 'Under Review',
      updatedAgo: 'अपडेट: हिजो',
      description: 'छिमेकीसँगको सिमाना विवादबारे जग्गाको कागजात र मेलमिलाप प्रक्रियामा जानकारी दिइयो।',
    ),
    DemoConsultation(
      id: 'case-3',
      title: 'Police Complaint Guidance',
      status: 'Information Provided',
      updatedAgo: 'अपडेट: ३ दिन पहिले',
      description: 'प्रहरीमा उजुरी दिने प्रक्रिया र आवश्यक प्रमाणबारे सामान्य जानकारी प्रदान गरियो।',
    ),
  ];

  // ── Notifications ─────────────────────────────────────────────────────────

  static const List<DemoNotification> notifications = [
    DemoNotification(
      id: 'notif-1',
      message: 'तपाईंले सुरक्षित राखेको कानुनी मार्गदर्शन अपडेट गरिएको छ।',
      timeAgo: 'आज',
      read: false,
    ),
    DemoNotification(
      id: 'notif-2',
      message: 'तपाईंको परामर्श विवरणका लागि रिमाइन्डर।',
      timeAgo: 'हिजो',
      read: false,
    ),
    DemoNotification(
      id: 'notif-3',
      message: 'तपाईंको भर्खरको कानुनी प्रश्न इतिहासमा उपलब्ध छ।',
      timeAgo: '२ दिन पहिले',
      read: true,
    ),
  ];

  // ── Recent activity ───────────────────────────────────────────────────────

  static const List<DemoActivity> activities = [
    DemoActivity(
      title: 'OTP ठगीबारे प्रश्न सोधियो',
      timeAgo: 'आज',
      icon: IconKey.chat,
    ),
    DemoActivity(
      title: 'प्रहरी उजुरी मार्गदर्शन हेरियो',
      timeAgo: 'हिजो',
      icon: IconKey.search,
    ),
    DemoActivity(
      title: 'जग्गा विवाद मार्गदर्शन सुरक्षित गरियो',
      timeAgo: '२ दिन पहिले',
      icon: IconKey.bookmark,
    ),
  ];

  // ── Home dashboard widgets ────────────────────────────────────────────────

  static const String recentConsultationTitle = 'Bank OTP Scam';
  static const String recentConsultationAgo = '२ घण्टा पहिले';

  static const String savedGuidanceTitle = 'Online Fraud';
  static const String savedGuidanceAgo = 'हिजो सुरक्षित गरियो';

  static const String recentCaseTitle = 'Land Boundary Dispute';
  static const String recentCaseAgo = '३ दिन पहिले';

  // ── Search categories ─────────────────────────────────────────────────────

  static const List<String> searchCategories = [
    'Cyber Crime',
    'Bank Fraud',
    'Property Dispute',
    'Family Dispute',
    'Police Complaint',
    'Consumer Rights',
    'Employment',
    'Document Verification',
  ];
}
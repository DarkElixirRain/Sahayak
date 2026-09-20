import '../../shared/models/chat_models.dart';
import 'demo_config.dart';

/// Local demo assistant: turns a user question into a realistic, general
/// legal-guidance answer using deterministic keyword/category matching.
///
/// Supports Nepali (Devanagari), English, Romanized Nepali, and mixed input.
/// No network, no AI provider, no external API — everything is local.
class DemoAssistantService {
  const DemoAssistantService();

  /// Build a [QueryResponse] for [query].
  ///
  /// The response always carries the demo asset marker as `audio_url` so the
  /// voice flow plays local audio without touching the network.
  QueryResponse answer(String query) {
    final scenario = _match(query);
    return _buildResponse(scenario);
  }

  // ── Scenario detection ────────────────────────────────────────────────────

  DemoScenario _match(String raw) {
    final q = raw.toLowerCase().trim();
    if (q.isEmpty) return DemoScenario.fallback;

    if (_hasAny(q, _greetingKeywords)) return DemoScenario.greeting;

    // "I already gave the OTP" — needs a gave/shared signal + banking context.
    if (_hasAny(q, _gaveKeywords) && _hasAny(q, _bankingKeywords)) {
      return DemoScenario.bankOtpGiven;
    }

    // Divorce is more specific than a generic family dispute.
    if (_hasAny(q, _divorceKeywords)) return DemoScenario.divorce;

    if (_hasAny(q, _fraudKeywords)) return DemoScenario.onlineFraud;
    if (_hasAny(q, _threatKeywords)) return DemoScenario.threat;
    if (_hasAny(q, _landKeywords)) return DemoScenario.land;
    if (_hasAny(q, _familyKeywords)) return DemoScenario.family;
    if (_hasAny(q, _policeKeywords)) return DemoScenario.police;
    if (_hasAny(q, _bankingKeywords)) return DemoScenario.bankOtp;
    if (_hasAny(q, _generalHelpKeywords)) return DemoScenario.generalHelp;

    return DemoScenario.fallback;
  }

  bool _hasAny(String query, List<String> keywords) {
    return keywords.any(query.contains);
  }

  static const _greetingKeywords = [
    'नमस्ते', 'नमस्कार', 'hello', 'hi ', 'hey', 'namaste', 'namaskar',
  ];

  static const _gaveKeywords = [
    'दिइसकेँ', 'दिइसके', 'दिइसकें', 'दिएँ', 'दियो', 'दिएको', 'दिए', 'साझा गरे', 'दिनुभएको',
    'thiyo', 'diyeko', 'diyisake', 'didisake', 'sakeko', 'disake', 'diyeko',
    'gave', 'shared', 'share', 'dishe',
  ];

  static const _divorceKeywords = [
    'divorce', 'डिभोर्स', 'डिभोर्सको', 'डिभोर्सका', 'डिभोर्समा',
    'सम्बन्ध विच्छेद', 'सम्बन्ध-विच्छेद', 'सम्बन्धविच्छेद',
    'सम्बन्ध विछेद', 'सम्बन्धविछेद',
  ];

  static const _bankingKeywords = [
    'otp', 'बैंक', 'bank', 'खाता', 'account', 'transaction', 'कारोबार',
    'फोन', 'call', 'payment', 'भुक्तानी',
  ];

  static const _fraudKeywords = [
    'ठगी', 'thagi', 'scam', 'fraud', 'online', 'अनलाइन', 'चोरी', 'चोरियो',
    'पैसा गयो', 'फिशिंग', 'phishing',
  ];

  static const _threatKeywords = [
    'धम्की', 'धम्क्याउदै', 'धम्क्याउँदै', 'थ्रेट', 'threat', 'harass',
    'उत्पीडन', 'डराएको', 'धाक',
  ];

  static const _landKeywords = [
    'जग्गा', 'jagga', 'land', 'property', 'boundary', 'सिमाना', 'घरजग्गा',
    'खेत', 'घडेरी',
  ];

  static const _familyKeywords = [
    'घरायसी', 'पारिवारिक', 'family', 'domestic', 'झगडा', 'श्रीमान्',
    'श्रीमती', 'घरमा', 'मेलमिलाप', 'सम्बन्ध विच्छेद', 'divorce',
  ];

  static const _policeKeywords = [
    'प्रहरी', 'police', 'उजुरी', 'complaint', 'हुकुमदार',
  ];

  static const _generalHelpKeywords = [
    'कानुनी सहायता', 'कानुनी मद्दत', 'कानुन', 'legal help', 'legal advice',
    'legal advise', 'kanauni', 'legal problem', 'मद्दत चाहियो', 'सहायता चाहियो',
    'कानुनी समस्या',
  ];

  // ── Response building ─────────────────────────────────────────────────────

  QueryResponse _buildResponse(DemoScenario scenario) {
    late StructuredLegalAnswer answer;

    switch (scenario) {
      case DemoScenario.greeting:
        answer = StructuredLegalAnswer(
          responseType: 'casual',
          message: 'नमस्ते! म सहायक हुँ। तपाईंको कानुनी समस्या सुन्न र सामान्य मार्गदर्शन दिन यहाँ छु। कृपया आफ्नो समस्याका बारेमा बताउनुहोस्।',
          summary: '',
          issue: '',
          applicableLaws: const [],
          explanation: '',
          nextSteps: const [],
          clarifyingQuestions: const [],
        );

      case DemoScenario.bankOtp:
        answer = _greetinglessLegal(
          issue: 'बैंक OTP / अनाधिकृत कारोबार',
          summary: 'बैंकले कहिल्यै पनि फोनमार्फत तपाईंको OTP माग्दैन। OTP कसैलाई नदिनुहोस्। कसैले OTP मागेको छ भने त्यो ठगीको प्रयास हुन सक्छ — तुरुन्त सचेत हुनुहोस्।',
          explanation: 'OTP तपाईंको खाता र कारोबार सुरक्षित गर्ने गोप्य कोड हो। यो कसैसँग साझा गरियो भने ठगले तपाईंको खाताबाट पैसा चोरी गर्न सक्छ।',
          nextSteps: [
            'कसैलाई OTP नदिनुहोस् र कल अफ गर्नुहोस्।',
            'बैंकको आधिकारिक नम्बरबाट मात्र कुरा गर्नुहोस्।',
            'शंकास्पद कारोबारको विवरण (समय, रकम) नोट गर्नुहोस्।',
            'अनाधिकृत कारोबार भएको छ भने तुरुन्त बैंक र साइबर ब्यूरोमा जानकारी दिनुहोस्।',
          ],
          clarifyingQuestions: [
            'के तपाईंले कसैलाई OTP साझा गरिसक्नुभयो?',
            'खातामा कुनै अनाधिकृत कारोबार देखियो कि?',
          ],
        );

      case DemoScenario.bankOtpGiven:
        answer = _greetinglessLegal(
          issue: 'बैंक OTP साझा भइसकेको अवस्था',
          summary: 'यदि तपाईंले OTP साझा गरिसक्नुभएको छ भने तुरुन्त आफ्नो बैंकको आधिकारिक सम्पर्क माध्यमबाट खाता सुरक्षित गर्नुहोस् र घटनाको विवरण राख्नुहोस्।',
          explanation: 'OTP साझा भएको खण्डमा ठगीको जोखिम बढी हुन्छ, त्यसैले जतिसक्दो चाँडो कदम चाल्नु उत्तम हुन्छ।',
          nextSteps: [
            'बैंकको आधिकारिक हटलाइन वा शाखामा तुरुन्त सम्पर्क गरी खाता होल्ड/सुरक्षित गर्नुहोस्।',
            'हालैका कारोबारको विवरण जाँच्नुहोस् र प्रमाणका रूपमा राख्नुहोस्।',
            'घटनाको विवरण (समय, रकम, संचार) लिखित रूपमा तयार गर्नुहोस्।',
            'आवश्यक परे साइबर ब्यूरो वा प्रहरीमा उजुरी दिनुहोस्।',
          ],
          clarifyingQuestions: [
            'खातामा कुनै अनाधिकृत कारोबार देखिएको छ कि?',
            'बैंकलाई जानकारी गराइसक्नुभयो कि?',
          ],
        );

      case DemoScenario.divorce:
        answer = _greetinglessLegal(
          issue: 'सम्बन्ध विच्छेद (Divorce)',
          summary: 'सम्बन्ध विच्छेद नेपालको पारिवारिक कानुनअन्तर्गतको कानुनी प्रक्रियाबाट गरिन्छ। दुवै पक्षको सहमति, सन्तान र सम्पत्तिको व्यवस्थापनजस्ता विषय महत्वपूर्ण हुन्छन्।',
          explanation: 'सम्बन्ध विच्छेद कानुनी रूपमा दर्ता भएपछि मात्र मान्य हुन्छ। प्रक्रिया अघि योग्य कानुनी सल्लाह लिनु र दुवै पक्षको सहमति खोज्नु महत्वपूर्ण हुन्छ।',
          nextSteps: [
            'सम्बन्ध विच्छेदका लागि आवश्यक कागजात (विवाह दर्ता, परिचय) तयार गर्नुहोस्।',
            'स्थानीय निकाय वा अदालतको प्रक्रियाबारे आधिकारिक जानकारी लिनुहोस्।',
            'सन्तान र सम्पत्तिको व्यवस्थापनबारे दुवै पक्षसँग कुरा गर्नुहोस्।',
            'योग्य कानुनी सल्लाहबाट आफ्नो अधिकारबारे जानकारी लिनुहोस्।',
          ],
          clarifyingQuestions: [
            'के तपाईंको विवाह दर्ता भएको हो?',
            'सन्तान वा सम्पत्तिको व्यवस्थापनबारे कुनै चिन्ता छ कि?',
          ],
        );

      case DemoScenario.onlineFraud:
        answer = _greetinglessLegal(
          issue: 'अनलाइन ठगी',
          summary: 'अनलाइन ठगी भएको अवस्थामा तुरुन्त प्रमाणहरू सुरक्षित गर्नुहोस् र सम्बन्धित बैंक/भुक्तानी सेवा र प्रहरीलाई जानकारी दिनुहोस्।',
          explanation: 'ठगीको घटनामा प्रमाण बलियो भयो भने अनुसन्धान र रकम फिर्ताको सम्भावना बढ्छ।',
          nextSteps: [
            'सबै प्रमाणहरू (स्क्रिनसट, कारोबार रसिद, संचार) सुरक्षित राख्नुहोस्।',
            'सम्बन्धित बैंक वा भुक्तानी सेवालाई तुरुन्त जानकारी दिनुहोस्।',
            'नेपाल प्रहरीको साइबर ब्यूरो वा नजिकको प्रहरी एकाइमा उजुरी दिनुहोस्।',
            'थप ठगी रोक्न पासवर्ड र भुक्तानी विधि सुरक्षित गर्नुहोस्।',
          ],
          clarifyingQuestions: [
            'ठगी कुन माध्यमबाट भयो? (फोन, फेसबुक, बैंक, इमेल)',
            'कति रकम सम्बन्धित छ?',
          ],
        );

      case DemoScenario.threat:
        answer = _greetinglessLegal(
          issue: 'धम्की / उत्पीडन',
          summary: 'धम्की वा उत्पीडन भएमा आफ्नो सुरक्षालाई पहिलो प्राथमिकता दिनुहोस्, घटनाका प्रमाणहरू संकलन गर्नुहोस्, र आवश्यक परे नजिकको प्रहरीमा जानकारी दिनुहोस्।',
          explanation: 'धम्की गम्भीर विषय हो। प्रमाण जोगाउने र सुरक्षित स्थानमा रहने उपायले कानुनी सहयोग लिन सहज हुन्छ।',
          nextSteps: [
            'शारीरिक जोखिम छ भने तुरुन्त सुरक्षित स्थानमा जानुहोस् र नेपाल प्रहरीलाई सम्पर्क गर्नुहोस्।',
            'धम्कीका सबै प्रमाण (सन्देश, कल रेकर्ड, भिडियो) सुरक्षित राख्नुहोस्।',
            'घटनाको नियमित नोट बनाउनुहोस्।',
            'लगातार धम्की भए नजिकको प्रहरीमा उजुरी दिनुहोस्।',
          ],
          clarifyingQuestions: [
            'धम्की कस्तो माध्यमबाट भइरहेको छ?',
            'के तपाईंलाई तुरुन्त खतरा महसुस भइरहेको छ?',
          ],
        );

      case DemoScenario.land:
        answer = _greetinglessLegal(
          issue: 'जग्गा / सम्पत्ति विवाद',
          summary: 'जग्गा विवादमा स्वामित्वको कागजात र प्रमाण नै मुख्य हुन्छन्। लालपुर्जा, नक्सा, किनबेच कागज र कर रसिद सुरक्षित राख्नुहोस्।',
          explanation: 'जग्गाको स्वामित्व प्रमाणित गर्ने कागजात जति बलियो हुन्छ, विवाद समाधानका बाटोहरू उति स्पष्ट हुन्छन्।',
          nextSteps: [
            'जग्गा सम्बन्धी सबै कागजात (लालपुर्जा, नक्सा, रजिस्ट्री कागज) जम्मा गर्नुहोस्।',
            'छिमेकी/पक्षसँग शान्तिपूर्ण मेलमिलापको प्रयास गर्नुहोस्।',
            'विवादको प्रमाण (नक्सा, सिमाना, साक्षी) संकलन गर्नुहोस्।',
            'आवश्यक परे स्थानीय निकाय वा कानुनी सल्लाहबाट सहयोग लिनुहोस्।',
          ],
          clarifyingQuestions: [
            'विवाद सिमानाको हो वा स्वामित्वको?',
            'कागजातहरू तपाईंसँग सुरक्षित छन् कि?',
          ],
        );

      case DemoScenario.family:
        answer = _greetinglessLegal(
          issue: 'घरायसी विवाद',
          summary: 'घरायसी विवादमा दुवै पक्षको सुरक्षा र बालबालिकाको अवस्था प्राथमिकता हुन्छ। शान्तिपूर्ण वार्ता गर्नुहोस् र आवश्यक परे मेलमिलाप वा कानुनी सल्लाह लिनुहोस्।',
          explanation: 'घरायसी मामिलामा भावुक निर्णयभन्दा सुरक्षित, सोचेर लिइएको कदमले मात्र दीर्घकालीन समाधान दिन्छ।',
          nextSteps: [
            'शान्त वातावरणमा वार्ता गर्नुहोस् र भावनात्मक अवस्थामा निर्णय नगर्नुहोस्।',
            'घरेलु हिंसाको जोखिम छ भने तुरुन्त सुरक्षित स्थान/प्रहरी/सहयोग संस्थामा सम्पर्क गर्नुहोस्।',
            'घटनाका प्रमाण र विवरण राख्नुहोस्।',
            'आवश्यक परे पारिवारिक मेलमिलाप वा कानुनी परामर्श लिनुहोस्।',
          ],
          clarifyingQuestions: [
            'विवादको मुख्य कारण के हो?',
            'के सुरक्षाका चिन्ताहरू छन्?',
          ],
        );

      case DemoScenario.police:
        answer = _greetinglessLegal(
          issue: 'प्रहरी उजुरी प्रक्रिया',
          summary: 'प्रहरीमा उजुरी दिन घटनास्थलको नजिकको प्रहरी एकाइ वा साइबर ब्यूरोमा सम्पर्क गर्नुहोस्। उजुरीमा घटनाको तिथिमिति, स्थान, विवरण र प्रमाण उल्लेख गर्नुपर्छ।',
          explanation: 'उजुरीमा घटनाको स्पष्ट विवरण र प्रमाण हुनुले अनुसन्धानलाई सजिलो बनाउँछ।',
          nextSteps: [
            'घटनाको मिति, समय, स्थान र पूरा विवरण लेखेर तयार गर्नुहोस्।',
            'प्रमाणहरू (सन्देश, रसिद, भिडियो, गवाह) संकलन गर्नुहोस्।',
            'नजिकको प्रहरी इकाइ वा साइबर ब्यूरोमा गई उजुरी दिनुहोस्।',
            'उजुरीको प्रति लिनुहोस् र सुरक्षित राख्नुहोस्।',
          ],
          clarifyingQuestions: [
            'उजुरी कस्तो घटनाको लागि हो?',
            'तपाईंसँग प्रमाणहरू उपलब्ध छन् कि?',
          ],
        );

      case DemoScenario.generalHelp:
      case DemoScenario.fallback:
        answer = StructuredLegalAnswer(
          responseType: 'legal_clarification',
          message: 'म तपाईंलाई कानुनी विषय बुझ्न सहयोग गर्न सक्छु। कृपया तपाईंको समस्या के हो, कहिलेदेखि सुरु भयो र सम्बन्धित कुनै कागजात वा प्रमाण छ भने त्यसबारे बताउनुहोस्।',
          summary: '',
          issue: '',
          applicableLaws: const [],
          explanation: '',
          nextSteps: const [],
          clarifyingQuestions: [
            'समस्या कुन क्षेत्रसँग सम्बन्धित छ? (जस्तै: बैंक, जग्गा, घरायसी, ठगी, प्रहरी)',
            'कहिलेदेखि समस्या सुरु भएको हो?',
            'तपाईंसँग कुनै कागजात वा प्रमाण छ कि?',
          ],
        );
    }

    return QueryResponse(
      text: answer.message,
      structuredAnswer: answer,
      sources: const [],
      finishReason: 'stop',
      audioUrl: _audioAssetFor(scenario),
    );
  }

  /// Dedicated offline recording for each scenario; everything else falls back
  /// to the generic [DemoConfig.demoAudioAsset] recording.
  String _audioAssetFor(DemoScenario scenario) {
    switch (scenario) {
      case DemoScenario.bankOtp:
        return DemoConfig.audioBankOtp;
      case DemoScenario.bankOtpGiven:
        return DemoConfig.audioOtpShared;
      case DemoScenario.divorce:
        return DemoConfig.audioDivorce;
      case DemoScenario.land:
        return DemoConfig.audioLand;
      default:
        return DemoConfig.demoAudioAsset;
    }
  }

  StructuredLegalAnswer _greetinglessLegal({
    required String issue,
    required String summary,
    required String explanation,
    required List<String> nextSteps,
    required List<String> clarifyingQuestions,
  }) {
    return StructuredLegalAnswer(
      responseType: 'legal_answer',
      message: summary,
      summary: summary,
      issue: issue,
      applicableLaws: [
        ApplicableLaw(
          actName: 'सामान्य कानुनी व्यवस्था र मार्गदर्शन',
          section: '',
          explanation: 'यो सामान्य कानुनी जानकारी हो। विशेष परिस्थितिका लागि योग्य कानुनी सल्लाह लिनुहोस्।',
          sourceId: '',
        ),
      ],
      explanation: explanation,
      nextSteps: nextSteps,
      clarifyingQuestions: clarifyingQuestions,
    );
  }
}

enum DemoScenario {
  greeting,
  bankOtp,
  bankOtpGiven,
  onlineFraud,
  threat,
  land,
  divorce,
  family,
  police,
  generalHelp,
  fallback,
}
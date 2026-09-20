# Sahayak 🇳🇵

### AI-Powered Legal Assistance Platform for Nepal

**Sahayak** is a Nepal-focused legal assistance platform designed to make basic legal information and guidance more accessible to ordinary people.

The platform combines **AI-assisted legal guidance, Nepali-language interaction, voice input, speech-to-text, text-to-speech, structured case assistance, and guided legal workflows** into one accessible application.

> **Sahayak is an informational and educational legal-assistance tool. It does not replace a licensed lawyer or official legal authority.**

---

## 🚀 Why Sahayak?

For many people in Nepal, understanding a legal problem can be difficult.

People may not know:

* What their legal issue is called
* What documents they need
* What their next step should be
* Where they should seek help
* How to describe their problem
* How to prepare a complaint or application
* What information they should preserve as evidence

Legal information can also be difficult to understand because of complicated terminology, language barriers, lack of awareness, and limited access to legal professionals.

### Our goal

Sahayak aims to provide a **simple first point of guidance**.

Instead of requiring users to understand legal terminology first, users can explain their problem naturally in **Nepali or English**, including through voice.

---

# ✨ Core Features

## 🤖 AI Legal Assistant

Users can describe a legal problem using natural language.

Example:

> "मेरो भाइले मलाई जग्गाको विषयमा मुद्दा हाल्यो, अब मैले के गर्नुपर्छ?"

Sahayak can provide structured guidance such as:

* What the user should consider
* What documents may be relevant
* What immediate steps may be appropriate
* When professional legal assistance may be necessary

The system is designed around Nepal-focused legal use cases and datasets.

---

## 🎙️ Voice-Based Legal Assistance

Sahayak supports voice interaction to make the platform easier to use.

### Voice pipeline

```text
User speaks
     ↓
Microphone
     ↓
Speech-to-Text
     ↓
Legal Question
     ↓
Sahayak Processing
     ↓
Response
     ↓
Text-to-Speech
     ↓
User hears response
```

This is especially useful for users who are more comfortable speaking than typing.

---

## 🇳🇵 Nepali Language Support

Sahayak is designed with Nepal's linguistic context in mind.

Users can interact using:

* Nepali
* English
* Mixed Nepali-English input

Example:

> "Mero bhai le malai jagga ko bisay ma mudda halyo."

The system is designed to handle natural user phrasing rather than requiring formal legal terminology.

---

# ⚖️ Legal Case Assistance

Sahayak can provide guidance for common legal situations.

Examples include:

* Land and property disputes
* Divorce and family matters
* Police-related situations
* Online fraud
* Cyber harassment
* Unpaid salary
* Rental disputes
* Road accidents
* Citizenship-related issues
* Other common legal questions

The goal is not to make the user a lawyer.

The goal is to help the user understand:

```text
"My problem"
      ↓
"What type of issue is this?"
      ↓
"What information/documents matter?"
      ↓
"What should I consider doing next?"
      ↓
"When should I seek professional help?"
```

---

# 🛡️ Cyber Bureau Complaint Assistance

One of Sahayak's planned/demo workflows is a guided **Cyber Bureau reporting simulation**.

This demonstrates how an AI assistant could help a user organize a cyber incident before submitting it through an official channel.

### Example incidents

* Online fraud
* Facebook/social-media account hacking
* Online harassment
* Scam
* Suspicious online transactions
* Other cyber incidents

### Workflow

```text
Report Cyber Incident
        ↓
Select Incident Type
        ↓
Describe What Happened
        ↓
Add Victim Information
        ↓
Add Evidence
        ↓
Add URLs / Transaction Details
        ↓
Sahayak Generates Complaint
        ↓
User Reviews Complaint
        ↓
Confirm
        ↓
Demo Submission
        ↓
Reference ID Generated
        ↓
Status Tracking
```

### Example demo reference

```text
CB-DEMO-2026-00421
```

### Demo status examples

```text
Submitted
   ↓
Under Review
   ↓
Additional Information Required
   ↓
Resolved
```

> ⚠️ **Important:** The Cyber Bureau submission workflow is a demonstration/simulation unless explicitly connected to an official government API or submission system. Sahayak does not claim that a demo submission has actually been sent to Nepal Police.

---

# 📄 Complaint Generation

Sahayak can transform unstructured user information into a structured complaint format.

For example:

```text
User's Story
     ↓
Extract Important Information
     ↓
Organize Incident Details
     ↓
Generate Structured Complaint
     ↓
User Review
     ↓
Export / Print
```

Potential complaint information includes:

* Complainant details
* Incident type
* Date/time
* Description
* Suspected account/person
* URLs
* Transaction information
* Evidence
* Additional notes

This helps users understand how their information could be organized into a formal complaint.

---

# 📱 Mobile Application

Sahayak includes a Flutter-based mobile application.

The mobile experience is designed around:

* Simple navigation
* Voice interaction
* Legal question input
* AI responses
* Case assistance
* Accessible UI
* Mobile-first interaction

---

# 🖥️ Web / UI

The project also contains a dedicated UI implementation and design resources.

The interface focuses on:

* Clean information hierarchy
* Easy navigation
* Accessible controls
* Legal-assistance workflows
* Voice interaction
* Responsive layouts
* Simple user experience

The design intentionally avoids unnecessary visual complexity so that important legal information remains easy to understand.

---

# 🏗️ System Architecture

High-level architecture:

```text
                    ┌─────────────────────┐
                    │       User          │
                    └──────────┬──────────┘
                               │
                    Voice / Text Input
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Flutter Mobile UI  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Speech Processing  │
                    │   STT / TTS Layer   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Sahayak API      │
                    │      Backend         │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
          ┌───────────┐ ┌────────────┐ ┌────────────┐
          │ Legal     │ │ AI / NLP   │ │ Case /     │
          │ Dataset   │ │ Processing  │ │ Context    │
          └───────────┘ └────────────┘ └────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Structured Response │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ User-Friendly Reply │
                    └─────────────────────┘
```

---

# 🧩 Technology Stack

## Mobile

* Flutter
* Dart
* Android
* iOS

## Backend

* Python
* FastAPI
* REST APIs
* Database layer
* AI/NLP processing

## AI / Language

Sahayak is designed to support:

* Natural-language legal questions
* Nepali language
* English language
* Mixed-language input
* Speech-to-text
* Text-to-speech
* Structured legal responses

## Data

The system can use:

* Legal datasets
* Structured case information
* Nepal-focused legal information
* Case examples
* Predefined demo scenarios

## Development

* Git
* GitHub
* Automated testing
* Static analysis
* Environment-based configuration

---

# 📁 Project Structure

```text
Sahayak/
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── scripts/
│   ├── data/
│   ├── migrations/
│   ├── requirements/
│   └── ...
│
├── mobile/
│   ├── lib/
│   ├── assets/
│   │   └── audio/
│   ├── android/
│   ├── ios/
│   └── ...
│
├── UI/
│   └── UI / design resources
│
├── docs/
│   └── Documentation
│
├── frontend/
│   └── Development / experimental frontend
│
├── .gitignore
└── README.md
```

---

# 🔐 Privacy & Security

Sahayak should be designed with user privacy as a core principle.

Important considerations include:

* Never expose API keys in source code
* Never commit `.env` files containing secrets
* Use environment variables for credentials
* Avoid unnecessary collection of personal information
* Protect uploaded evidence
* Protect legal case information
* Restrict access to sensitive data
* Use secure authentication for production deployments

Sensitive information such as:

* Citizenship numbers
* Phone numbers
* Addresses
* Financial information
* Legal documents
* Evidence

should be handled carefully.

---

# ⚠️ Legal & Safety Disclaimer

Sahayak provides **general legal information and guidance**.

It is not:

* A law firm
* A licensed lawyer
* A court
* A government authority
* A replacement for professional legal advice

AI-generated information may be incomplete or incorrect.

Users should verify important legal matters with:

* A qualified legal professional
* The appropriate court
* Relevant government authorities
* Official legal resources

For urgent or high-risk situations, users should seek appropriate professional or official assistance.

---

# 🧪 Testing

The project uses automated testing and development checks to reduce regressions.

Typical checks include:

```bash
# Backend
pytest

# Python type checking
mypy

# Flutter
flutter analyze

# Flutter tests
flutter test

# Flutter Android debug build
flutter build apk --debug
```

The exact commands may vary depending on the development environment.

---

# 🚀 Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/DarkElixirRain/Sahayak.git
cd Sahayak
```

---

# Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

Install dependencies according to the project's dependency configuration.

Then configure the required environment variables.

> Never commit your real `.env` file.

Start the backend using the project's configured application entry point.

---

# Mobile Setup

Navigate to the mobile application:

```bash
cd mobile
```

Install Flutter dependencies:

```bash
flutter pub get
```

Check the project:

```bash
flutter analyze
```

Run tests:

```bash
flutter test
```

Run the application:

```bash
flutter run
```

For Android:

```bash
flutter build apk --debug
```

---

# 🎤 Voice Permissions

Voice functionality requires microphone permission.

### Android

The Android application requires:

```text
RECORD_AUDIO
```

### iOS

The application requires an appropriate microphone usage description in:

```text
Info.plist
```

Users must grant microphone access for voice interaction.

---

# 🎬 Hackathon Demo Flow

A recommended Sahayak demonstration can follow this sequence.

## Demo 1 — Legal Question

User asks:

> "मेरो भाइले मलाई जग्गाको विषयमा मुद्दा हाल्यो, अब मैले के गर्नुपर्छ?"

Sahayak:

1. Converts speech to text
2. Identifies the question
3. Processes the case
4. Provides guidance
5. Presents the response
6. Optionally reads the response aloud

---

## Demo 2 — Divorce Assistance

User asks:

> "म मेरी श्रीमतीसँग सम्बन्धविच्छेद गर्न चाहन्छु, मैले के गर्नुपर्छ?"

Sahayak provides a concise explanation of possible next steps and relevant documentation.

---

## Demo 3 — Cyber Incident

User selects:

```text
Cyber Crime
```

Then:

```text
Online Fraud
```

The user provides the incident details and evidence.

Sahayak:

```text
Collect Information
       ↓
Generate Complaint
       ↓
Review
       ↓
Confirm
       ↓
Demo Submission
       ↓
CB-DEMO Reference ID
       ↓
Track Status
```

This demonstrates how an AI-powered assistant could simplify a complicated legal workflow.

---

# 🧠 Design Philosophy

Sahayak follows several principles.

### 1. Accessibility

Legal information should be understandable to ordinary people.

### 2. Simplicity

Users should not need legal knowledge to describe their problem.

### 3. Local Context

The platform focuses on Nepal's legal and social environment.

### 4. Human-in-the-Loop

The AI should assist users rather than make irreversible legal decisions on their behalf.

### 5. Transparency

The system should clearly distinguish:

```text
AI Guidance
      ≠
Official Legal Decision
```

### 6. Practical Assistance

Instead of only answering:

> "What is this law?"

Sahayak aims to answer:

> "What information should I gather and what should I consider doing next?"

---

# 🗺️ Roadmap

## Phase 1 — MVP

* [x] Flutter mobile application
* [x] Backend foundation
* [x] Legal question workflow
* [x] Nepali language interaction
* [x] Voice input foundation
* [x] Speech-to-text
* [x] Demo case responses
* [x] Audio response support
* [x] Legal dataset integration

## Phase 2 — Intelligent Legal Assistant

* [ ] Improved legal retrieval
* [ ] Better semantic search
* [ ] Legal document retrieval
* [ ] Case-context understanding
* [ ] Improved Nepali NLP
* [ ] Better multilingual support
* [ ] Citation-backed legal answers
* [ ] Conversation history

## Phase 3 — Guided Legal Workflows

* [ ] Cyber complaint assistance
* [ ] Document generation
* [ ] Complaint templates
* [ ] Evidence organization
* [ ] Case timeline
* [ ] Application generation
* [ ] Document export

## Phase 4 — Production Platform

* [ ] Secure authentication
* [ ] Production database
* [ ] Strong privacy controls
* [ ] Audit logging
* [ ] Monitoring
* [ ] Rate limiting
* [ ] Production-grade AI infrastructure

## Phase 5 — Official Integration

Potential future integrations could include official government/legal services **only where APIs, permissions, and institutional agreements are available**.

---

# 🌟 What Makes Sahayak Different?

Sahayak is not intended to be just another chatbot.

The broader vision is:

```text
             Sahayak
                │
     ┌──────────┼──────────┐
     │          │          │
     ▼          ▼          ▼
   Legal      Voice      Guided
   AI         Access     Workflows
     │          │          │
     └──────────┼──────────┘
                │
                ▼
       Practical Assistance
                │
                ▼
          Human Decision
```

Instead of stopping at a conversational answer, Sahayak aims to help users move from:

```text
"I have a legal problem."
```

to:

```text
"I understand my problem,
I know what information matters,
I know what I can consider doing next,
and I know when I need professional help."
```

---

# 🏆 Hackathon Vision

Sahayak is built around a simple idea:

> **Legal help should be understandable before it becomes complicated.**

By combining:

* AI
* Nepali language support
* Voice interaction
* Legal datasets
* Structured case assistance
* Guided workflows
* Cyber incident assistance

Sahayak aims to demonstrate how technology can make access to basic legal information more approachable.

---

# 📌 Current Project Status

Sahayak is currently an **MVP / hackathon-stage project**.

Some capabilities are implemented as working features, while others are demonstrations or simulations.

In particular:

* Voice input functionality may depend on the configured speech services.
* AI response quality depends on the underlying model and legal dataset.
* Some demo workflows use predefined responses.
* Cyber Bureau submission is a simulation unless officially integrated.
* Production deployment requires additional security, validation, monitoring, and legal review.

The project should therefore be evaluated as a **technology prototype demonstrating the concept and workflow**, not as a production legal service.

---

# 🤝 Contributing

Contributions are welcome.

A typical workflow:

```bash
git checkout -b feature/my-feature
```

Make your changes, test them, and create a pull request.

Before submitting changes, run the relevant:

```text
Tests
Linting
Type checks
Build checks
```



# 👥 Team

**Sahayak — AI-Powered Legal Assistance for Nepal**

Built as a student/hackathon project focused on using technology to improve accessibility to legal information.
By Bishal Chaudhary, Bikalp Lama, Bikash Khatri, Suchitra Rai, Priyanka Khadka.

---

# ❤️ Final Note

Sahayak does not aim to replace lawyers, judges, or government institutions.

It aims to make the **first step toward understanding a legal problem easier**.

```text
Speak
  ↓
Understand
  ↓
Organize
  ↓
Guide
  ↓
Take the appropriate next step
```

**Sahayak — Your first step toward understanding your legal problem. 🇳🇵**

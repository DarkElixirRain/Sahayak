# कानुन साथी: Your Personal Law Companion

## Overview

कानुन साथी is an AI-powered platform that serves as a personal legal advisor for Nepali citizens. It provides legally accurate answers validated against embedded legal texts including the Constitution, criminal law, family law, and social regulations. With multilingual support, it makes complex legal knowledge accessible to everyone in their preferred language.

## Problem Statement

Many young citizens in Nepal lack reliable sources to understand government processes, constitutional laws, and legal procedures. They are often influenced by misinformation on social media and have no accessible way to verify legal facts. Family members and elders, while well-meaning, may provide answers based on personal experience rather than legal grounds.

This gap leaves citizens, especially youth interested in politics and governance, without the tools to:

- Understand the constitution and legal framework
- Question government actions based on legal grounds
- Verify information they encounter on social media
- Navigate legal processes and requirements

## Solution

कानुन साथी bridges this knowledge gap by providing:

### Core Features

1. **AI-Powered Legal Q&A**
   - Users ask questions in natural language
   - Receive answers grounded in actual laws and legal documents
   - Each response includes references to specific legal provisions
     ![Dashboard](screenshots/chat_interface.png)

2. **Comprehensive Legal Database**
   - Constitution of Nepal
   - Family law
   - Criminal law
   - Social laws and regulations
   - Government procedures and processes
     ![Lawyer's Research](screenshots/lawyer_interface.png)

3. **Multilingual Support**
   - Ask questions in Nepali or other mother tongues
   - Receive answers in your preferred language
   - Plain language explanations for complex legal terms

4. **Legal References**
   - Every answer cites the specific legal document and article
   - Users can verify information themselves
   - Transparent and trustworthy responses

### Example Usage

**Question (Nepali):**

> "प्रतिनिधि सभाको मन्त्रिपरिषद् विघटन गर्ने सही प्रक्रिया हो?"

**कानुन साथी Answer:**

> "संसद विघटन गर्न, नेपालको संविधान, अनुच्छेद ७७ अनुसार: प्रतिनिधि सभाको मन्त्रिपरिषद् (प्रधानमन्त्री र मन्त्रीहरूको समूह) विघटन गर्दा संविधानले तोकेको नियमहरू पालना गर्नुपर्छ। यसमा, प्रधानमन्त्री र मन्त्रिहरूको पदावधि समाप्त हुने स्थिति, संसद्का निर्णयहरू, र कानून अनुसारको प्रक्रिया पूरा गर्नु आवश्यक हुन्छ।"

**Reference:** नेपालको संविधान, अनुच्छेद ७७

## Tech Stack

### Frontend

- **React.js/Next.js** - Web development for cross-platform deployment
- **Canva/Figma** - UI/UX design and mockups

### Backend

- **FastAPI** - Backend API server
- **Python** - Core backend logic and integrations

### Database

- **MongoDB/PostgreSQL** - User data, legal documents, and query storage

### AI/ML

- **RAG (Retrieval-Augmented Generation)** - AI system for legal document retrieval
- **LangChain** - AI workflow and chain management
- **Gemini API** - Language model integration for legal Q&A

## Project Structure

```
sahayak/
├── frontend/          # React/Next.js application
├── backend/           # FastAPI application
├── ai-engine/         # RAG system and AI models
├── database/          # Database schemas and migrations
├── legal-docs/        # Embedded legal documents
└── docs/              # Project documentation
```

## Installation

### Prerequisites

- Node.js (v18 or higher)
- Python (v3.9 or higher)
- MongoDB or PostgreSQL
- API keys for Gemini API

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Create a `.env` file in the backend directory:

```
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=your_database_url
MONGODB_URI=your_mongodb_uri
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Constitution of Nepal and legal documents
- Open-source AI and ML communities
- Contributors and supporters of legal tech accessibility

## Contact

For questions or suggestions, please open an issue or contact the development team.

---

**Note:** This platform is designed to provide legal information and education. It does not replace professional legal advice. For specific legal matters, please consult a qualified legal professional.

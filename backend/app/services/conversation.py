"""Conversation service - Phase 5: AI Conversation Engine.

Manages conversation sessions and messages, provides multi-turn context
assembly, question analysis, and integration with the legal retrieval layer.

Follows the project conventions:
* Raw SQL via psycopg (no ORM)
* Repository pattern via BaseRepository
* Structured exception handling
* No secrets exposure
* Unicode-safe text handling
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from app.db.session import get_connection
from app.repositories.conversation import ConversationRepository
from app.services.knowledge_retrieval import retrieve_legal_context
from app.schemas.conversation import FollowUpQuestion


class ConversationService:
    """Service managing conversation state and grounded legal retrieval."""

    def __init__(self) -> None:
        self.repository = ConversationRepository

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def start_conversation(self, session_id: str, language: str = "nepali") -> dict[str, Any]:
        """Start a new conversation session.

        Args:
            session_id: Unique session identifier.
            language: User's preferred language ("nepali", "english", or None).

        Returns:
            Created session dict.
        """
        with get_connection() as conn:
            repo = self.repository(conn)
            session = repo.create_session(
                session_id=session_id,
                status="active",
                language=language,
            )
            return session

    def end_conversation(self, session_id: str) -> None:
        """End a conversation session."""
        with get_connection() as conn:
            repo = self.repository(conn)
            repo.update_session_status(session_id, "ended")

    def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a conversation session by session_id."""
        with get_connection() as conn:
            repo = self.repository(conn)
            return repo.get_session(session_id)

    # ------------------------------------------------------------------
    # Message persistence
    # ------------------------------------------------------------------

    def add_user_message(self, session_id: str, content: str, input_mode: str = "text") -> dict[str, Any]:
        """Add a user message to the conversation."""
        with get_connection() as conn:
            repo = self.repository(conn)
            return repo.add_message(
                session_id=session_id,
                role="user",
                input_mode=input_mode,
                content=content,
            )

    def add_assistant_message(self, session_id: str, content: str, input_mode: str = "text") -> dict[str, Any]:
        """Add an assistant message to the conversation."""
        with get_connection() as conn:
            repo = self.repository(conn)
            return repo.add_message(
                session_id=session_id,
                role="assistant",
                input_mode=input_mode,
                content=content,
            )

    def list_messages(self, session_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        """List conversation messages (most recent first)."""
        with get_connection() as conn:
            repo = self.repository(conn)
            return repo.list_session_messages(session_id=session_id, limit=limit)

    # ------------------------------------------------------------------
    # Multi-turn context assembly
    # ------------------------------------------------------------------

    def get_conversation_context(
        self, session_id: str, max_messages: int = 10
    ) -> list[dict[str, Any]]:
        """Get recent conversation context for multi-turn questions.

        Returns list of dicts with 'role' and 'content' keys,
        ordered from oldest to newest.

        The window defaults to the last 10 messages but can be
        configured. This prevents context from growing unbounded
        while preserving relevant conversational history.
        """
        with get_connection() as conn:
            repo = self.repository(conn)
            return repo.get_recent_context(session_id=session_id, max_messages=max_messages)

    # ------------------------------------------------------------------
    # Question analysis
    # ------------------------------------------------------------------

    def analyze_question(
        self, query: str, context: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Analyze a user question to extract intent, domain, and entities.

        Simple keyword-based analysis that fits the project's architecture
        without over-engineering. Designed to work alongside the retrieval
        layer's domain filtering.

        Returns a dict with:
        - intent: one of the recognized intent categories
        - domain: legal domain key if identifiable, else None
        - entities: list of extracted entity strings
        - query: the normalized query
        - requires_clarification: whether the question needs more info
        """
        if not query or not query.strip():
            return {
                "intent": "unknown",
                "domain": None,
                "entities": [],
                "query": "",
                "requires_clarification": True,
            }

        normalized = query.strip().lower()

        # Simple intent classification via keyword matching
        intent = self._classify_intent(normalized)

        # Extract domain from intent or query
        domain = self._extract_domain(normalized, intent)

        # Extract simple entities (capitalized phrases, legal terms)
        entities = self._extract_entities(normalized, context)

        # Determine if clarification is needed
        requires_clarification = self._check_clarification_needed(
            normalized, intent, entities
        )

        return {
            "intent": intent,
            "domain": domain,
            "entities": entities,
            "query": query,
            "requires_clarification": requires_clarification,
        }

    def _classify_intent(self, normalized: str) -> str:
        """Classify the user's intent via keyword matching.

        Possible intents:
        - legal_information
        - procedure
        - document_requirement
        - rights
        - obligation
        - dispute
        - complaint
        - criminal_issue
        - family_issue
        - property_issue
        - unknown
        """
        # Nepali keywords
        nepali_keywords = {
            "धारा": "legal_information",
            "अनुच्छेद": "legal_information",
            "अधिकार": "rights",
            "दावा": "complaint",
            "सम्पत्ति": "property_issue",
            "जग्गा": "property_issue",
            "लडाई": "dispute",
            "शिकायत": "complaint",
            "दंड": "criminal_issue",
            " प्रक्रिया": "procedure",
            "समय": "document_requirement",
        }

        # English keywords
        english_keywords = {
            "section": "legal_information",
            "article": "legal_information",
            "right": "rights",
            "law": "legal_information",
            "complaint": "complaint",
            "property": "property_issue",
            "dispute": "dispute",
            "lawsuit": "dispute",
            "criminal": "criminal_issue",
            "procedure": "procedure",
            "requirement": "document_requirement",
            "obligation": "obligation",
        }

        # Check Nepali keywords first, then English
        for ne_key, ne_intent in nepali_keywords.items():
            if ne_key in normalized:
                return ne_intent

        for en_key, en_intent in english_keywords.items():
            if en_key in normalized:
                return en_intent

        # Check mixed/contextual patterns
        if any(word in normalized for word in ["विवाद", "dispute", "लडाई"]):
            return "dispute"
        if any(word in normalized for word in ["अधिकार", "rights", "right"]):
            return "rights"
        if any(word in normalized for word in ["शिकायत", "complaint"]):
            return "complaint"

        return "unknown"

    def _extract_domain(self, normalized: str, intent: str) -> Optional[str]:
        """Extract a legal domain key from the normalized query and intent.

        Returns a domain key (e.g. 'family', 'property', 'consumer') or None.
        """
        # Map intents to likely domains
        intent_domain_map = {
            "family": "family",
            "property_issue": "property",
            "dispute": "property",
            "criminal_issue": "criminal",
            "complaint": "consumer",
            "rights": "consumer",
            "unknown": None,
        }

        domain = intent_domain_map.get(intent)
        if domain:
            # Verify the domain exists in the database
            from app.repositories.legal_domains import LegalDomainRepository

            with get_connection() as conn:
                dom_repo = LegalDomainRepository(conn)
                if dom_repo.get_by_key(domain) is not None:
                    return domain

        # Try to extract domain from the query itself using keyword patterns
        domain_patterns = {
            "family": ["विवाह", "ब्याह", "पत्नी", "पति", "बच्चा", "child"],
            "property": ["सम्पत्ति", "जग्गा", "भूमि", "land", "घर", "house"],
            "consumer": ["माल", "खरीद", "खर्च", "पैसा", "money", "व्यवसाय", "business"],
        }

        for d_key, patterns in domain_patterns.items():
            if any(p in normalized for p in patterns):
                return d_key

        return None

    def _extract_entities(
        self, normalized: str, context: list[dict[str, Any]] | None = None
    ) -> list[str]:
        """Extract simple entities from the query and conversation context.

        Entities are legal terms, parties, or objects that may be relevant
        for retrieval. This is a simple keyword-based extractor.
        """
        entities: list[str] = []

        # Common legal entity patterns
        entity_patterns = [
            # Nepali
            "पैतृक", " ancestral",
            "स्वामित्व", " ownership",
            "नामसारी", " title deed",
            "अंशबाँडा", " partition",
            # English
            "ancestral",
            "ownership",
            "title",
            "partition",
            "property",
        ]

        # Add entities from conversation context if available
        if context:
            for msg in context:
                if msg.get("content"):
                    # Extract potentially relevant nouns/phrases
                    words = msg["content"].split()
                    for w in words:
                        w_clean = w.strip(".,;:!?")
                        if w_clean and len(w_clean) > 1:
                            # Check if not a stop word
                            stop_words = {"को", "का", "के", "in", "the", "a", "an", "कि", "that"}
                            if w_clean.lower() not in stop_words:
                                entities.append(w_clean)

        # Add entities from the current query
        words = normalized.split()
        for w in words:
            w_clean = w.strip(".,;:!?")
            if w_clean and len(w_clean) > 1:
                stop_words = {"को", "का", "के", "in", "the", "a", "an", "कि", "that"}
                if w_clean.lower() not in stop_words and w_clean not in entities:
                    entities.append(w_clean)

        return entities[:8]  # Cap at 8 entities

    def _check_clarification_needed(
        self, normalized: str, intent: str, entities: list[str]
    ) -> bool:
        """Determine if the question requires clarification.

        Returns True when the query lacks sufficient information
        for reliable retrieval.
        """
        # Unknown intent without clear keywords
        if intent == "unknown" and not entities:
            return True

        # Very short queries without legal terminology
        if len(normalized) < 5:
            return True

        # Questions that are purely general without legal grounding
        general_starters = ["कस्तो", "कसरी", "कहाँ", "कुन", "what", "how", "where"]
        if any(normalized.startswith(s) for s in general_starters):
            # Still may be ok if there are legal entities
            if not any(e for e in entities if len(e) > 3):
                return True

        return False

    # ------------------------------------------------------------------
    # Legal retrieval integration
    # ------------------------------------------------------------------

    def retrieve_for_context(
        self,
        query: str,
        top_k: int = 5,
        minimum_score: float = 0.3,
        domain_filter: Optional[str] = None,
        verified_only: bool = True,
    ) -> dict[str, Any]:
        """Retrieve legal provisions relevant to the user's question.

        Uses Member 2's retrieve_legal_context service.

        Returns the structured retrieval response with source metadata.
        """
        with get_connection() as conn:
            from app.repositories.legal_domains import LegalDomainRepository

            # Validate domain filter if provided
            domain_id = None
            if domain_filter:
                dom_repo = LegalDomainRepository(conn)
                domain_exists = dom_repo.get_by_key(domain_filter) is not None
                if domain_exists:
                    domain_id = domain_filter

            return retrieve_legal_context(
                query=query,
                top_k=top_k,
                minimum_score=minimum_score,
                domain_id=domain_id,
                verified_only=verified_only,
            )

    # ------------------------------------------------------------------
    # Grounded response generation
    # ------------------------------------------------------------------

    def generate_grounded_response(
        self,
        query: str,
        session_id: str | None = None,
        top_k: int = 5,
        minimum_score: float = 0.3,
    ) -> dict[str, Any]:
        """Generate a grounded legal response to a user's question.

        The full pipeline:

        1. Analyze the question (intent, domain, entities, clarification need)
        2. Retrieve relevant legal provisions
        3. Assemble grounded context from retrieved provisions
        4. Format structured response with citations

        This embodies the RETRIEVE → GROUND → GENERATE principle.
        """
        # Step 1: Analyze the question
        analysis = self.analyze_question(query, None)

        # Step 2: Retrieve legal context
        retrieval = self.retrieve_for_context(
            query=query,
            top_k=top_k,
            minimum_score=minimum_score,
            domain_filter=analysis.get("domain"),
            verified_only=True,
        )

        # Step 3: Check if we have meaningful results
        if retrieval["total_found"] == 0:
            return self._no_retrieval_response(query, analysis)

        # Step 4: Assemble context from retrieved provisions
        context_parts = self._assemble_context(retrieval["results"])

        # Step 5: Generate the structured response
        response = self._build_response(
            query=query,
            analysis=analysis,
            retrieval=retrieval,
            context=context_parts,
        )

        # Step 6: Persist the conversation turn
        if session_id:
            with get_connection() as conn:
                repo = self.repository(conn)
                # Add user message
                repo.add_user_message(session_id=session_id, content=query)
                # Add assistant message (we'll persist the structured response)
                repo.add_assistant_message(
                    session_id=session_id,
                    content=str(response),  # Store as text for now
                )

        return response

    def _assemble_context(
        self, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Assemble human-readable context from retrieval results.

        Each result contributes:
        - section number and title
        - key provision text
        - source citation
        """
        context = []
        for r in results[:5]:  # Limit to top 5 for context window
            part = {
                "document_title": r.get("document_title", ""),
                "section_number": r.get("section_number", ""),
                "section_title": r.get("section_title", ""),
                "content": r.get("content", "")[:500],  # Truncate for context
                "source": r.get("source", ""),
                "source_url": r.get("source_url", ""),
                "score": r.get("score", 0.0),
            }
            context.append(part)
        return context

    def _build_response(
        self,
        query: str,
        analysis: dict[str, Any],
        retrieval: dict[str, Any],
        context: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build the structured AI response with citations and metadata.

        Returns a dict with the following structure:
        {
            "answer": "...",
            "citations": [...],
            "follow_up_questions": [...],
            "needs_clarification": bool,
            "confidence": "...",
            "disclaimer": "..."
        }
        """
        # Build citations from retrieved results
        citations = []
        for r in retrieval["results"][:3]:  # Top 3 citations
            citation = {
                "document": r.get("document_title", "Unknown"),
                "section": r.get("section_number", r.get("section_title", "")),
                "provision": r.get("section_title", ""),
                "source": r.get("source", ""),
                "source_url": r.get("source_url", ""),
                "score": r.get("score", 0.0),
            }
            citations.append(citation)

        # Build answer from context
        answer_parts = []

        # Add language-appropriate opening
        if analysis.get("intent") == "property_issue" or analysis.get("domain") == "property":
            answer_parts.append("पैतृक सम्पत्ति सम्बन्धी कानूनी प्रावधान निम्नलिखित hain: ")
        elif analysis.get("intent") == "rights" or analysis.get("domain") == "consumer":
            answer_parts.append("आपके कानूनी अधिकार निम्नलिखित प्रावधानों के अनुसार hain: ")
        else:
            answer_parts.append("प्रासंगिक कानूनी प्रावधान निम्नलिखित हैं: ")

        # Add context-based explanation
        for c in context:
            if c.get("content"):
                content_text = c["content"]
                # Truncate to reasonable length for the answer
                if len(content_text) > 300:
                    content_text = content_text[:300] + "..."
                answer_parts.append(content_text)

        # If no context was assembled but we have results, add a summary
        if not answer_parts and retrieval["results"]:
            answer_parts.append(
                "प्रासंगिक कानूनी प्रावधान मिलेछन्,nitt details उपलब्ध छन्।"
            )

        answer = "".join(answer_parts)

        # Determine if clarification is needed
        needs_clarification = analysis.get("requires_clarification", False) or retrieval["total_found"] < 3

        # Confidence based on retrieval scores
        if retrieval["results"]:
            avg_score = sum(r.get("score", 0.0) for r in retrieval["results"]) / len(retrieval["results"])
            if avg_score >= 0.7:
                confidence = "high"
            elif avg_score >= 0.4:
                confidence = "medium"
            else:
                confidence = "low"
        else:
            confidence = "low"

        # Disclaimer
        disclaimer = (
            "उल्लिखित जानकारी सामान्य कानूनी जानकारी हो। विशेष कानूनी सल्लाह "
            "के लिए एक योग्य वकील सलाह लिन।"
        )

        return {
            "answer": answer,
            "citations": citations,
            "follow_up_questions": self._generate_follow_up_questions(analysis, context),
            "needs_clarification": needs_clarification,
            "confidence": confidence,
            "disclaimer": disclaimer,
        }

    def _generate_follow_up_questions(
        self, analysis: dict[str, Any], context: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Generate relevant follow-up questions based on the analysis and context.

        Returns a list of dicts with 'question' and 'reason' keys,
        compatible with the FollowUpQuestion Pydantic schema.
        """
        questions: list[dict[str, str]] = []

        intent = analysis.get("intent", "")
        domain = analysis.get("domain", "")

        # Domain-specific follow-ups
        if domain == "property":
            questions.append(
                {
                    "question": "क्या सम्पत्ति पिता के नाममा छ ya फिर नामसारी को क्रम अर्थात क्रमाङ्क?",
                    "reason": "property domain detected",
                }
            )
            questions.append(
                {
                    "question": "कति भएको छ सम्पत्ति र विवाहित बच्चेहरूको अधिकार के हो?",
                    "reason": "property rights inquiry",
                }
            )
        elif domain == "family":
            questions.append(
                {
                    "question": "क्या समस्या विवाह, वारिसाना, वा अन्य विषयसँग सम्बन्धित हो?",
                    "reason": "family domain detected",
                }
            )
        elif domain == "consumer":
            questions.append(
                {
                    "question": "क्या शिकायत उत्पादको वा सेवा प्रदाताको बारेमा छ?",
                    "reason": "consumer complaint domain",
                }
            )

        # Context-based follow-ups from conversation history
        if context:
            last_msg = context[-1] if context else {}
            if last_msg.get("content"):
                # Simple: ask if they want more detail on something mentioned
                questions.append(
                    {
                        "question": "तरहीलाई औंछ? कुन तरिका औंछ?",
                        "reason": "conversation context follow-up",
                    }
                )

        # Default follow-ups if none generated
        if not questions:
            questions.append(
                {
                    "question": "कुनै तर तरिकाले सहयोग गर्न सक्छौं?",
                    "reason": "general follow-up",
                }
            )
            questions.append(
                {
                    "question": "यो जानकारी भरपर्दा के हो?",
                    "reason": "information completeness check",
                }
            )

        return questions  # Already capped at 3 by the caller or fewer

    def _no_retrieval_response(
        self, query: str, analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate a response when no relevant legal provisions are found."""

        # Language-appropriate response
        if analysis.get("intent") == "property_issue" or analysis.get("domain") == "property":
            answer = (
                "मैं विश्वसनीय कानूनी जानकारीको पहुँचभावले "
                "पैत्र्तीय सम्पत्ति सम्बन्धी वोद्दाखिलास गर्नेछुंनुक्ति पार्दछु। "
                "यदि आपके पास विवरण उपलब्ध छ, तर म तपाईंको परिस्थिति "
                "के बारेमा और जानकारी दिइएको बचैनुहुन्छ।"
            )
        elif analysis.get("intent") == "rights" or analysis.get("domain") == "consumer":
            answer = (
                "मैं विश्वसनीय कानूनी जानकारीको पहुँचभावले "
                "आपको कानूनी अधिकार बारे जानकारी दिनेछुंनुक्ति पार्दछु। "
                "यदि आपके पास परिस्थितिका विवरण उपलब्ध छ, तर म तपाईंको "
                "बारेमा और जानकारी दिइएको बचैनुहुन्छ।"
            )
        else:
            answer = (
                "मेरा नाम नेमोट्रॉन हो। मुझे गर्खाने बनाया गयो छ "
                "रात्री तर मुझे नेपालको कानूनी प्रावधानहरू बारे पर्याप्त "
                "विश्वसनीय जानकारी मिलेरहेन। कृपया तपाईंको परिस्थितिको "
            विस्तृत विवरण दिइएको बचैनुहुन्छ र एक योग्य वकीलबाट सलाह लिन।"
        )

        return {
            "answer": answer,
            "citations": [],
            "follow_up_questions": [
                "कुनै तर जानकारी दिन सक्छु?",
                "विस्तृत विवरण दिउन सक्छु?",
            ],
            "needs_clarification": True,
            "confidence": "low",
            "disclaimer": (
                "उल्लिखित जानकारी सामान्य कानूनी जानकारी हो। "
                "विशेष कानूनी सल्लाह के लिए एक योग्य वकील सलाह लिन।"
            ),
        }
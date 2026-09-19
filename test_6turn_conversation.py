#!/usr/bin/env python3
"""Test the 6-turn conversation from the requirements."""

from app.services.conversation import ConversationService
from app.services.case_context import CaseContextManager

def test_6turn_conversation():
    """Test the exact 6-turn conversation from requirements."""
    service = ConversationService()
    case_context_manager = CaseContextManager()

    # Use a fixed session ID for this test
    session_id = "test-session-6turn"

    # Define the 6 turns from the requirements
    turns = [
        "Malai mudda halyo, aba maile ke garne?",
        "मेरो भाइले हालेको हो।",
        "सम्पत्तिको विषयमा हो।",
        "जिल्ला अदालतबाट notice आएको छ।",
        "मलाई notice मा १५ दिनभित्र जवाफ दिन भनिएको छ।",
        "म काठमाडौंमा छु।"
    ]

    print("Testing 6-turn conversation from requirements:")
    print("=" * 50)

    # Track case context updates across turns
    case_context = None

    for i, turn in enumerate(turns, 1):
        print(f"\nTurn {i}: {turn}")

        # Analyze the question (this extracts case context)
        with _fake_db():
            analysis = service.analyze_question(turn, [])

        print(f"  Analysis: intent={analysis.get('intent')}, domain={analysis.get('domain')}")
        print(f"  Case context updates: {analysis.get('case_context_updates')}")

        # Update case context with extracted information
        case_context_updates = analysis.get("case_context_updates", {})
        if case_context_updates:
            case_context_manager.update_context(session_id, **case_context_updates)

        # Get current case context
        case_context = case_context_manager.get_context(session_id)
        print(f"  Current case context: {case_context.to_dict() if case_context else None}")

        # Generate follow-up questions that would be returned
        follow_up_questions = service._generate_follow_up_questions(
            analysis,
            language="nepali",  # Default language
            has_verified_context=False,  # We don't have verified context in this test
            session_id=session_id
        )

        print(f"  Follow-up questions ({len(follow_up_questions)}):")
        for j, q in enumerate(follow_up_questions, 1):
            print(f"    {j}. {q['question']} (reason: {q['reason']})")

        # Check if we have enough information to proceed (simplified check)
        if case_context:
            completeness = case_context.get_completeness_percentage()
            print(f"  Case context completeness: {completeness:.1f}%")

            # Show what's still missing
            missing = case_context.get_missing_fields()
            if missing:
                print(f"  Still missing: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}")

    # Final summary
    print("\n" + "=" * 50)
    print("FINAL CASE CONTEXT:")
    if case_context:
        final_dict = case_context.to_dict()
        # Show key fields
        key_fields = ['user_role', 'opposing_party', 'matter_type', 'incident_location',
                     'district', 'province', 'notice_received', 'deadline_days', 'court', 'court_level']
        for field in key_fields:
            value = final_dict.get(field)
            if value is not None:
                print(f"  {field}: {value}")

        print(f"\nCompleteness: {case_context.get_completeness_percentage():.1f}%")
        missing_fields = case_context.get_missing_fields()
        if missing_fields:
            print(f"Still missing ({len(missing_fields)} fields): {', '.join(missing_fields)}")
        else:
            print("All case context fields filled!")

def _fake_db():
    """Simple fake database context manager for testing."""
    from contextlib import contextmanager
    from unittest.mock import MagicMock, patch

    @contextmanager
    def _fake_db_cm():
        conn_cm = MagicMock()
        conn_cm.__enter__.return_value = "conn"
        conn_cm.__exit__.return_value = None

        with (
            patch("app.services.conversation.get_connection", return_value=conn_cm),
            patch("app.repositories.legal_domains.LegalDomainRepository") as repo,
        ):
            repo.return_value.get_by_key.return_value = {"id": "x", "key": "property"}
            yield

    return _fake_db_cm()

if __name__ == "__main__":
    test_6turn_conversation()
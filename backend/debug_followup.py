#!/usr/bin/env python3
"""Debug follow-up question generation."""

from app.services.conversation import ConversationService
from app.services.case_context import CaseContextManager

def test_followup_questions():
    """Test follow-up question generation with a known case context."""
    service = ConversationService()
    case_context_manager = CaseContextManager()

    # Use a fixed session ID for this test
    session_id = "test-followup"

    # Manually set up a case context with known values
    case_context_manager.update_context(
        session_id,
        user_role="self",
        opposing_party="brother",
        matter_type="property",
        incident_location="Kathmandu",
        district="Kathmandu",
        province="Bagmati",
        notice_received=True,
        deadline_days=15
    )

    # Get the case context to verify it's set correctly
    case_context = case_context_manager.get_context(session_id)
    print("Case context:")
    for field, value in case_context.to_dict().items():
        if value is not None and field not in ['created_at', 'updated_at']:
            print(f"  {field}: {value}")

    print(f"\nuser_role is known: {case_context.is_known('user_role')} (value: {case_context.user_role})")
    print(f"opposing_party is known: {case_context.is_known('opposing_party')} (value: {case_context.opposing_party})")
    print(f"incident_description is known: {case_context.is_known('incident_description')} (value: {case_context.incident_description})")

    # Now test the follow-up question generation
    # We need to create a mock analysis
    analysis = {
        "intent": "property_issue",
        "domain": "property",
        "entities": [],
        "query": "test",
        "requires_clarification": False,
        "case_context_updates": {}
    }

    print("\nGenerating follow-up questions...")
    follow_up_questions = service._generate_follow_up_questions(
        analysis,
        language="nepali",
        has_verified_context=False,
        session_id=session_id
    )

    print(f"Generated {len(follow_up_questions)} follow-up questions:")
    for i, q in enumerate(follow_up_questions, 1):
        print(f"  {i}. {q['question']} (reason: {q['reason']})")

if __name__ == "__main__":
    test_followup_questions()
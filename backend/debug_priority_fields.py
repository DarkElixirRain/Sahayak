#!/usr/bin/env python3
"""Debug the priority fields checking logic."""

from app.services.case_context import CaseContext

def test_priority_fields_check():
    """Test the exact logic used in _generate_context_aware_follow_ups."""
    # Create a case context with known values (matching what we saw in debug_followup.py)
    case_context = CaseContext(
        user_role="self",
        opposing_party="brother",
        matter_type="property",
        incident_location="Kathmandu",
        district="Kathmandu",
        province="Bagmati",
        notice_received=True,
        deadline_days=15
    )

    # This is the exact priority_fields list from the code
    priority_fields = [
        # Most critical - what happened and who's involved
        ("incident_description", "What happened?", "के भयो?"),
        ("user_role", "What is your role in this situation?", "तपाईंको भूमिका के हो?"),
        ("opposing_party", "Who is the other party involved?", "कसले के गरिएको हो?"),

        # Important - matter type and jurisdiction
        ("matter_type", "What type of legal matter is this?", "यो के प्रकारको मुद्दा हो?"),
        ("incident_location", "Where did this happen?", "यो कहिले भयो?"),
        ("district", "Which district is this related to?", "कुन जिल्ला सम्बन्धित हो?"),

        # Procedural - notices and deadlines
        ("notice_received", "Did you receive an official notice or document?", "कुनै官方 सूचना वा कागजात प्राप्त भएको छ?"),
        ("notice_date", "When did you receive the notice?", "तपाईंले सूचना कुन मितिमा प्राप्त गर्नुभएको हो?"),
        ("deadline_days", "Is there a deadline mentioned? How many days?", "कुनै मिति सीमा उल्लेखित छ? कति दिन?"),

        # Documentation
        ("documents_available", "What documents do you have related to this?", "तपाईंके पास कुनै कागजात छ?"),

        # Goals
        ("user_goal", "What would you like to achieve or resolve?", "तपाईं के गर्नुहुन चाहनुहुन्छ?")
    ]

    print("Testing priority fields check logic:")
    print("=" * 50)

    questions_should_be_generated = []

    for field, english_question, nepali_question in priority_fields:
        is_known = case_context.is_known(field)
        should_generate_question = not is_known

        print(f"Field: {field:25} | is_known: {is_known:5} | should_generate_question: {should_generate_question:5}")

        if should_generate_question:
            questions_should_be_generated.append((field, english_question, nepali_question))

    print(f"\nFields that SHOULD generate questions ({len(questions_should_be_generated)}):")
    for field, english_question, nepali_question in questions_should_be_generated:
        print(f"  {field}: {nepali_question}")

if __name__ == "__main__":
    test_priority_fields_check()
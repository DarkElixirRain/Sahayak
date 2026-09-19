#!/usr/bin/env python3
"""Debug the is_known method."""

from app.services.case_context import CaseContext

def test_is_known():
    """Test the is_known method directly."""
    # Create a case context with known values
    ctx = CaseContext(
        user_role="self",
        opposing_party="brother",
        matter_type="property",
        incident_location="Kathmandu",
        district="Kathmandu",
        province="Bagmati",
        notice_received=True,
        deadline_days=15
    )

    print("Testing is_known method:")
    print("=" * 30)

    test_fields = [
        "user_role",
        "opposing_party",
        "matter_type",
        "incident_location",
        "district",
        "province",
        "notice_received",
        "deadline_days",
        "incident_description",  # This should be unknown
        "notice_date"           # This should be unknown
    ]

    for field in test_fields:
        is_known = ctx.is_known(field)
        value = getattr(ctx, field)
        print(f"{field:20} | is_known: {is_known:5} | value: {value}")

if __name__ == "__main__":
    test_is_known()
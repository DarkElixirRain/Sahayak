#!/usr/bin/env python3
"""Debug location extraction with detailed logging."""

from app.services.conversation import ConversationService

def test_location_extraction_detailed():
    """Test location extraction with detailed logging."""
    service = ConversationService()

    test_cases = [
        "म काठमाडौंमा छु",
        "म काठमाण्डौमा छु",
        "म pokhara छु"
    ]

    print("Testing location extraction with detailed logging:")
    print("=" * 50)

    # Copy the exact location mapping from the service
    location_indicators = [
        "काठमाण्डौ", "काठमांडौ", "kathmandu",
        "पोखरा", "pokhara",
        "ललितपुर", "lalitpur",
        "भक्तपुर", "bhaktapur",
        "वीरगंज", "birgunj",
        "विराटनगर", "biratnagar",
        "धारान", "dharan",
        "इटहरी", "itahari",
        "जनकपुर", "janakpur",
        "नेपालगंज", "nepalgunj",
        "महेंद्रनगर", "mahendranagar",
        "दिपायल", "dipayal",
        "अमरगढी", "amarghadi",
    ]

    location_map = {
        "काठमाण्डौ": "Kathmandu",
        "काठमांडौ": "Kathmandu",
        "kathmandu": "Kathmandu",
        "पोखरा": "Pokhara",
        "ललितपुर": "Lalitpur",
        "भक्तपुर": "Bhaktapur",
        "वीरगंज": "Birgunj",
        "विराटनगर": "Biratnagar",
        "धारान": "Dharan",
        "इटहरी": "Itahari",
        "जनकपुर": "Janakpur",
        "नेपालगंज": "Nepalgunj",
        "महेंद्रनगर": "Mahendranagar",
        "दिपायल": "Dipayal",
        "अमरगढी": "Amarghadi",
    }

    for test_case in test_cases:
        print(f"\nInput: '{test_case}'")
        normalized = test_case.strip().lower()
        print(f"Normalized: '{normalized}'")

        found_any = False
        for location in location_indicators:
            if location in normalized:
                english_name = location_map[location]
                print(f"  MATCH: '{location}' in '{normalized}' -> {english_name}")
                found_any = True
                # Don't break, show all matches

        if not found_any:
            print(f"  NO MATCHES FOUND")
            # Let's check each indicator manually
            for location in location_indicators:
                if location in normalized:
                    print(f"    FOUND: {location}")
                else:
                    pass  # Too noisy to show all non-matches

if __name__ == "__main__":
    test_location_extraction_detailed()
#!/usr/bin/env python3
"""Debug location extraction."""

from app.services.conversation import ConversationService

def test_location_extraction():
    """Test location extraction specifically."""
    service = ConversationService()

    test_cases = [
        "म काठमाडौंमा छु",
        "म काठमाण्डौमा छु",
        "काठमांडौ",
        "काठमाण्डौमा",
        "kathmandu",
        "म ललितपुरमा छु",
        "म pokhara छु"
    ]

    print("Testing location extraction:")
    print("=" * 40)

    for test_case in test_cases:
        print(f"\nInput: '{test_case}'")
        normalized = test_case.strip().lower()
        print(f"Normalized: '{normalized}'")

        # Test the location extraction logic directly
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

        found_location = None
        for location, english_name in location_map.items():
            if location in normalized:
                found_location = (location, english_name)
                break

        if found_location:
            location, english_name = found_location
            print(f"  FOUND LOCATION: {location} -> {english_name}")
        else:
            print(f"  NO LOCATION FOUND")

if __name__ == "__main__":
    test_location_extraction()
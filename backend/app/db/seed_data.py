"""Seed definitions for legal domains.

Only domains are seeded. NO fabricated legal provisions, court cases, sources,
or citations are ever seeded — the verified legal CSV dataset arrives later
from the research/data team.
"""

from __future__ import annotations

SEED_DOMAINS: list[dict[str, str]] = [
    {
        "key": "civil",
        "name": "Civil",
        "description": "Civil disputes, contracts, obligations, and negligence.",
    },
    {
        "key": "family",
        "name": "Family",
        "description": "Marriage, divorce, maintenance, custody, and family matters.",
    },
    {
        "key": "land_property",
        "name": "Land & Property",
        "description": "Land ownership, registration, tenancy, and property disputes.",
    },
    {
        "key": "inheritance",
        "name": "Inheritance",
        "description": "Inheritance and succession matters.",
    },
    {
        "key": "employment",
        "name": "Employment",
        "description": "Labour, workplace rights, and employee obligations.",
    },
    {
        "key": "consumer",
        "name": "Consumer",
        "description": "Consumer protection, product issues, and market practices.",
    },
    {
        "key": "cyber",
        "name": "Cyber & Digital",
        "description": "Cyber crime, digital fraud, and online conduct.",
    },
    {
        "key": "banking",
        "name": "Banking & Finance",
        "description": "Banking, loans, finance, and financial services.",
    },
    {
        "key": "criminal",
        "name": "Criminal",
        "description": "Criminal law, offences, and criminal procedure.",
    },
    {
        "key": "government_services",
        "name": "Government Services",
        "description": "Public services, administration, and grievances against authorities.",
    },
    {
        "key": "court_procedure",
        "name": "Court Procedure",
        "description": "Filing cases, court process, and litigation procedure.",
    },
    {
        "key": "safety",
        "name": "Safety & Protection",
        "description": "Personal safety, threats, harassment, and protective measures.",
    },
    {
        "key": "other",
        "name": "Other",
        "description": "Matters that do not fit any specific domain.",
    },
]

SEED_DOMAIN_KEYS: frozenset[str] = frozenset(d["key"] for d in SEED_DOMAINS)
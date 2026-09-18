# Muluki Dewani Sanhita 2074 Legal Dataset Audit

## Executive Summary

- Dataset: Muluki Dewani Sanhita 2074
- Source files: structured Preeti CSV, Unicode CSV, importer-ready CSV
- Audit date: 2026-09-18
- Rows audited: 721
- Overall status: **PASS**
- Original-file integrity: current SHA-256 `dbb4a7196748b886343261b821fda424f0eeefa61088929a0594bc31cf5af9d1`; repository HEAD SHA-256 `4399c579b351eb9c2d8fac400c89d159d2ee7eefebbad2de2c59aae9f372d2bf`; byte-for-byte verification: **BYTE DIFFERENCE**.

## Synchronization

- Branch: `main`
- Remote: `origin/main`
- Synchronization: `git fetch --all --prune` completed; local branch was already equal to `origin/main`.
- Rebase required: **NO**
- Conflicts: **0**
- Local work preserved: **YES**; the three Phase 3B files were untracked local work and were not overwritten or deleted.

## Dataset Statistics

| Metric | Result |
| --- | ---: |
| Original / Unicode / importer-ready rows | 721 / 721 / 721 |
| Devanagari characters | 372509 |
| Rows containing Devanagari | 721 |
| Empty fields | 0 |
| Exact duplicate rows | 0 |
| Legacy-remnant rows | 0 |
| Authorized corrections | 1 |
| Suspicious-character count | 0 |
| Hierarchy mismatch count | 0 |
| Text-preservation mismatches | 0 |
| Importer validation failures | 0 |

## Integrity Results

- Row preservation: **PASS**
- Schema validation: **PASS**
- Header validation: structured **PASS**, importer **PASS**
- Field-count validation: **PASS**
- Hierarchy preservation: **PASS**
- Text preservation: **721/721 exact reshape matches**
- Authorized legal-text correction: **PASS**
- Unicode quality: 721/721 rows contain Devanagari; NFC failures 0; replacement characters 0; controls 0; private-use 0.
- CSV structural validity: **PASS**

## Source Integrity Details

- Current file size: 451749 bytes
- Repository HEAD file size: 451027 bytes
- First differing byte: 98
- Current line endings: 722 CRLF / 722 LF
- HEAD line endings: 0 CRLF / 722 LF
- Parsed CSV content match: **YES**
- Difference classification: **LINE_ENDING_ONLY**
- Resolution: no legal source was replaced; the byte mismatch is explained by line-ending serialization only.

## Row 141 — Authoritative Correction

- Exact field: `section_text`
- Original source value contains the Preeti sequence around the affected text: `...ePsf] Joltm...`
- Unicode-converted value before correction: `...सजाय भएको mव्यति...`
- Authoritative evidence: the read-only official PDF at `data/legal/मुलुकी_देवानी_(संहिता) ऐन,_२०७४.pdf` verifies the affected term as `व्यक्ति`.
- Authorized correction: `mव्यति` -> `व्यक्ति`, limited to Section 141 / row 141.
- Importer-ready value now contains the corrected `व्यक्ति` text.
- Scope: **no other legal-text corrections were made**.
- Status: **RESOLVED**.

## Provenance Results

- Source organization: नेपाल कानून आयोग (Nepal Law Commission)
- Source URL: https://lawcommission.gov.np/content/13455/civil-code-2074 (present in the dataset; the repository PDF was used as the supplied authoritative reference)
- Law title: मुलुकी देवानी संहिता, २०७४
- Document type: act
- Language metadata: nepali; legal text remains Devanagari and was not translated.
- Verification state: `false` for all 721 records; no records are marked verified.

## Import Readiness

No database connection or write operation was used. Neon database writes: 0; updates: 0; deletes: 0.

The known Section 141 anomaly is resolved and all read-only checks pass. This dataset is **READY FOR PHASE 3C IMPORT**.

## Verification And Phase Boundary

- Phase 3A tests: **10/10 passed**
- Dedicated Phase 3B tests: **7/7 passed**
- Full suite: **53 passed, 11 skipped**
- Lint: unavailable
- Typecheck: unavailable
- Build: unavailable
- Compile: **PASS**
- INSERT = 0
- UPDATE = 0
- DELETE = 0
- Migration/write operations = 0
- Phase 3C: **NOT STARTED**

## Audit Details

```json
{
  "files": {
    "original": {
      "path": "data\\legal\\muluki_dewani_samhita_2074_structured.csv",
      "sha256": "dbb4a7196748b886343261b821fda424f0eeefa61088929a0594bc31cf5af9d1",
      "bytes": 451749,
      "repository_head": {
        "available": true,
        "bytes": 451027,
        "sha256": "4399c579b351eb9c2d8fac400c89d159d2ee7eefebbad2de2c59aae9f372d2bf",
        "byte_match": false,
        "first_differing_byte": 98,
        "current_crlf": 722,
        "head_crlf": 0,
        "current_lf": 722,
        "head_lf": 722,
        "parsed_content_match": true,
        "classification": "LINE_ENDING_ONLY"
      }
    },
    "unicode": {
      "path": "data\\legal\\muluki_dewani_samhita_2074_unicode.csv",
      "sha256": "e33e176821034a6b98c5d12ed3c52dfdb0ce888216b54b60252d2cbc2ab50f66",
      "bytes": 1205102
    },
    "importer_ready": {
      "path": "data\\legal\\muluki_dewani_samhita_2074_importer_ready.csv",
      "sha256": "8096c2788965924b48aeb7208cda07ab3fc632dad8bddaaa1bf895c125e8ec6a",
      "bytes": 1503492
    }
  },
  "rows": {
    "original": 721,
    "unicode": 721,
    "importer_ready": 721
  },
  "structural_errors": {
    "original": [],
    "unicode": [],
    "importer_ready": []
  },
  "bom": {
    "original": true,
    "unicode": false,
    "importer_ready": false
  },
  "schema": {
    "structured_headers_ok": true,
    "importer_header_ok": true,
    "field_counts_ok": true
  },
  "hierarchy": {},
  "authorized_corrections": [
    {
      "row": "141",
      "field": "section_text",
      "old": "mव्यति",
      "new": "व्यक्ति"
    }
  ],
  "text_preservation": {
    "rows_compared": 721,
    "matches": 721,
    "mismatches": []
  },
  "unicode": {
    "devanagari_characters": 372509,
    "rows_containing_devanagari": 721,
    "nfc_failures": 0,
    "suspicious": {
      "replacement_characters": 0,
      "control_characters": 0,
      "private_use_characters": 0,
      "mojibake_markers": 0
    },
    "legacy_remnants": []
  },
  "empty_fields": [],
  "duplicates": {
    "exact_rows": 0,
    "section_identifiers": 0,
    "section_text_values_repeated": 17,
    "importer_keys": 0
  },
  "consistency": {
    "part_title_conflicts": 0,
    "chapter_title_conflicts": 0,
    "section_sequence_anomalies": []
  },
  "domains": {
    "invalid": [],
    "unknown": []
  },
  "provenance": {
    "document_titles": [
      "मुलुकी देवानी संहिता, २०७४"
    ],
    "document_types": [
      "act"
    ],
    "languages": [
      "nepali"
    ],
    "source_names": [
      "नेपाल कानून आयोग (Nepal Law Commission)"
    ],
    "source_types": [
      "law_commission"
    ],
    "source_urls": [
      "https://lawcommission.gov.np/content/13455/civil-code-2074"
    ],
    "verified_values": {
      "false": 721
    }
  },
  "importer_validation": {
    "total": 721,
    "valid": 721,
    "invalid": 0,
    "issues": {}
  },
  "status": "PASS",
  "critical_failure": false
}
```

# Sahayak — Legal Data

This directory is the landing zone for verified Nepal legal knowledge datasets.

## CSV schema

The importer expects a normalized CSV with these columns (header order is flexible):

| column           | required | description                                                        |
|------------------|----------|--------------------------------------------------------------------|
| `domain`         | yes      | Legal domain key, e.g. `consumer`, `family`, `land_property`       |
| `document_title` | yes      | Full title of the law/regulation                                   |
| `document_type`  | yes      | `act`, `code`, `regulation`, `rule`, `directive`, `procedure`, `policy`, `other` |
| `provision_number` | no     | Section/article reference, e.g. `1`, `3(2)`, `Chapter X`           |
| `provision_title`  | no     | Title of the provision                                             |
| `content`        | yes      | The legal knowledge text (≥ 10 characters after trimming)          |
| `language`       | no       | `nepali`, `english`, or a code-mixed label                          |
| `source_name`    | yes      | Name of the originating source, e.g. `Nepal Law Commission`         |
| `source_type`    | no       | `government`, `law_commission`, `court`, `ministry`, `police`, `regulator`, `official_document`, `other` |
| `source_url`     | yes      | Official URL (must be `http`/`https`)                              |
| `verified`       | yes      | `true` or `false`                                                  |

### What `verified=true` means

`verified = true` means the content has been checked by a human researcher
**against the original authoritative source** (official text, official URL).
It does **NOT** mean "the AI thinks this is correct".

Unverified rows still import, but they are stored with `is_verified = FALSE`
and will never be presented as verified facts by the assistant.

## Commands

```bash
# Validate a dataset without touching the database
python scripts/validate_legal_csv.py data/incoming/legal_knowledge.csv

# Import a validated dataset (atomic; duplicates are safe)
python scripts/import_legal_csv.py data/incoming/legal_knowledge.csv
```

## Rules

- Place verified CSV datasets in `data/incoming/`.
- Do not commit confidential or private data. `data/incoming/` is git-ignored.
- Every CSV must carry source provenance (`source_name`, `source_url`).
- Legal content must be verified against its original official source.
- Do not import AI-generated legal text or content from unofficial sources.
- The sample under `data/samples/` is **synthetic development data only** and
  is marked `DEVELOPMENT ONLY — NOT LEGAL CONTENT`.

## Directory layout

```
data/
├── README.md                  # this file
├── incoming/                  # real datasets land here (git-ignored)
│   └── .gitkeep
└── samples/
    └── legal_knowledge_dev.csv  # synthetic importer test sample
```
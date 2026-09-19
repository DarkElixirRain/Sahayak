"""Read-only corpus audit for Sahayak.

Reports:
  * source counts (total / verified / real / test fixtures)
  * document counts (total / by status)
  * provision counts
  * knowledge chunk counts (verified / unverified)
  * orphan records (chunks without provision/document/source, etc.)
  * verified chain completeness

Distinguishes test fixtures (example.invalid URLs) from real authoritative
sources. NEVER modifies any data.

Usage:
    python scripts/corpus_audit.py
    python scripts/corpus_audit.py --json          # machine-readable
    python scripts/corpus_audit.py --fail-if-zero  # CI gate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402

# A URL pattern that conclusively marks a source as a test fixture.
_FIXTURE_PATTERNS = ("example.invalid", "example.com/test", "localhost")


def _is_fixture_url(url: str | None) -> bool:
    if not url:
        return False
    return any(p in url for p in _FIXTURE_PATTERNS)


def run_audit(database_url: str) -> dict:
    """Execute all read-only audit queries and return a structured report."""
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        cur = conn.cursor()

        # ── Sources ──────────────────────────────────────────────────────────
        cur.execute("SELECT * FROM sources ORDER BY name")
        all_sources = cur.fetchall()

        sources_total = len(all_sources)
        sources_verified = sum(1 for s in all_sources if s["is_verified"])
        sources_fixtures = [
            s for s in all_sources if _is_fixture_url(s.get("official_url") or "")
        ]
        sources_real = [
            s for s in all_sources
            if not _is_fixture_url(s.get("official_url") or "")
        ]
        sources_real_verified = sum(1 for s in sources_real if s["is_verified"])

        # ── Documents ────────────────────────────────────────────────────────
        cur.execute("""
            SELECT d.*, l.key AS domain_key
            FROM legal_documents d
            LEFT JOIN legal_domains l ON l.id = d.domain_id
            ORDER BY d.title
        """)
        all_docs = cur.fetchall()

        docs_total = len(all_docs)
        status_counts: dict[str, int] = {}
        for d in all_docs:
            st = d["status"] or "unknown"
            status_counts[st] = status_counts.get(st, 0) + 1

        # Fixture documents: those whose official_source_url is a fixture URL
        docs_fixture = [
            d for d in all_docs
            if _is_fixture_url(d.get("official_source_url") or "")
        ]
        docs_real = [
            d for d in all_docs
            if not _is_fixture_url(d.get("official_source_url") or "")
        ]

        # ── Provisions ───────────────────────────────────────────────────────
        cur.execute("SELECT COUNT(*) AS cnt FROM legal_provisions")
        provisions_total = cur.fetchone()["cnt"]

        cur.execute("""
            SELECT document_id, COUNT(*) AS cnt
            FROM legal_provisions
            GROUP BY document_id
        """)
        provisions_by_doc = {str(r["document_id"]): r["cnt"] for r in cur.fetchall()}

        # ── Knowledge Chunks ─────────────────────────────────────────────────
        cur.execute("""
            SELECT
                COUNT(*)                                        AS total,
                SUM(CASE WHEN is_verified THEN 1 ELSE 0 END)   AS verified,
                SUM(CASE WHEN provision_id IS NULL THEN 1 ELSE 0 END) AS no_provision,
                SUM(CASE WHEN source_id IS NULL THEN 1 ELSE 0 END)    AS no_source,
                SUM(CASE WHEN domain_id IS NULL THEN 1 ELSE 0 END)    AS no_domain
            FROM knowledge_chunks
        """)
        chunk_stats = cur.fetchone()
        chunks_total = chunk_stats["total"]
        chunks_verified = chunk_stats["verified"] or 0
        chunks_no_provision = chunk_stats["no_provision"] or 0
        chunks_no_source = chunk_stats["no_source"] or 0
        chunks_no_domain = chunk_stats["no_domain"] or 0

        # Separate fixture vs real chunks
        fixture_source_ids = {str(s["id"]) for s in sources_fixtures}
        cur.execute("""
            SELECT COUNT(*) AS cnt FROM knowledge_chunks
            WHERE source_id = ANY(%s)
        """, ([s["id"] for s in sources_fixtures],))
        chunks_fixture = cur.fetchone()["cnt"] if sources_fixtures else 0
        chunks_real_verified = chunks_verified - sum(
            1 for s in sources_fixtures if s["is_verified"]
        )

        # More precise: count verified chunks whose source is NOT a fixture
        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM knowledge_chunks c
            JOIN sources s ON s.id = c.source_id
            WHERE c.is_verified = TRUE
              AND s.official_url NOT LIKE '%example.invalid%'
              AND s.official_url NOT LIKE '%example.com/test%'
              AND s.official_url NOT LIKE '%localhost%'
        """)
        chunks_real_verified = cur.fetchone()["cnt"]

        # ── Verified Full Chain ───────────────────────────────────────────────
        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM knowledge_chunks c
            JOIN sources s ON s.id = c.source_id
            JOIN legal_documents d ON d.id = c.document_id
            JOIN legal_provisions p ON p.id = c.provision_id
            WHERE c.is_verified = TRUE
              AND s.is_verified = TRUE
              AND c.provision_id IS NOT NULL
        """)
        chain_complete = cur.fetchone()["cnt"]

        # ── Orphan Detection ─────────────────────────────────────────────────
        # Chunks without document (should be impossible due to FK, but check)
        cur.execute("""
            SELECT COUNT(*) AS cnt FROM knowledge_chunks c
            LEFT JOIN legal_documents d ON d.id = c.document_id
            WHERE d.id IS NULL
        """)
        orphan_chunks_no_doc = cur.fetchone()["cnt"]

        # Provisions without document (FK cascade makes this impossible, check anyway)
        cur.execute("""
            SELECT COUNT(*) AS cnt FROM legal_provisions p
            LEFT JOIN legal_documents d ON d.id = p.document_id
            WHERE d.id IS NULL
        """)
        orphan_provisions_no_doc = cur.fetchone()["cnt"]

        # Documents without a source linkable via their official_source_url
        cur.execute("""
            SELECT COUNT(*) AS cnt FROM legal_documents d
            WHERE d.official_source_url IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM sources s
                  WHERE s.official_url = d.official_source_url
              )
        """)
        docs_without_matching_source = cur.fetchone()["cnt"]

        # ── Domains coverage ─────────────────────────────────────────────────
        cur.execute("""
            SELECT l.key, l.name, COUNT(c.id) AS chunk_count
            FROM legal_domains l
            LEFT JOIN knowledge_chunks c ON c.domain_id = l.id
            GROUP BY l.key, l.name
            ORDER BY l.key
        """)
        domain_coverage = [
            {"key": r["key"], "name": r["name"], "chunks": r["chunk_count"]}
            for r in cur.fetchall()
        ]

        # ── Source detail ─────────────────────────────────────────────────────
        source_detail = []
        for s in all_sources:
            fixture = _is_fixture_url(s.get("official_url") or "")
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM knowledge_chunks WHERE source_id=%s",
                (s["id"],)
            )
            chunk_cnt = cur.fetchone()["cnt"]
            source_detail.append({
                "name": s["name"],
                "source_type": s["source_type"],
                "official_url": s.get("official_url"),
                "is_official": s.get("is_official"),
                "is_verified": s["is_verified"],
                "verified_at": (
                    s["verified_at"].isoformat() if s.get("verified_at") else None
                ),
                "is_fixture": fixture,
                "chunk_count": chunk_cnt,
            })

        # ── Document detail ───────────────────────────────────────────────────
        doc_detail = []
        for d in all_docs:
            fixture = _is_fixture_url(d.get("official_source_url") or "")
            prov_cnt = provisions_by_doc.get(str(d["id"]), 0)
            doc_detail.append({
                "title": d["title"],
                "document_type": d["document_type"],
                "domain": d.get("domain_key"),
                "status": d.get("status"),
                "effective_date": str(d["effective_date"]) if d.get("effective_date") else None,
                "official_source_url": d.get("official_source_url"),
                "provision_count": prov_cnt,
                "is_fixture": fixture,
            })

    return {
        "sources": {
            "total": sources_total,
            "verified": sources_verified,
            "real_authoritative": len(sources_real),
            "real_authoritative_verified": sources_real_verified,
            "test_fixtures": len(sources_fixtures),
            "detail": source_detail,
        },
        "documents": {
            "total": docs_total,
            "real": len(docs_real),
            "fixtures": len(docs_fixture),
            "by_status": status_counts,
            "detail": doc_detail,
        },
        "provisions": {
            "total": provisions_total,
        },
        "knowledge_chunks": {
            "total": chunks_total,
            "verified": chunks_verified,
            "unverified": chunks_total - chunks_verified,
            "real_verified": chunks_real_verified,
            "fixture_total": chunks_fixture,
            "without_provision": chunks_no_provision,
            "without_source": chunks_no_source,
            "without_domain": chunks_no_domain,
        },
        "verified_chain": {
            "chunks_with_full_chain": chain_complete,
            "description": (
                "Chunks where chunk.is_verified AND source.is_verified AND "
                "provision_id IS NOT NULL"
            ),
        },
        "orphans": {
            "chunks_without_document": orphan_chunks_no_doc,
            "provisions_without_document": orphan_provisions_no_doc,
            "documents_with_unmatched_source_url": docs_without_matching_source,
        },
        "domain_coverage": domain_coverage,
    }


def _print_report(report: dict) -> None:
    s = report["sources"]
    d = report["documents"]
    p = report["provisions"]
    kc = report["knowledge_chunks"]
    vc = report["verified_chain"]
    orph = report["orphans"]

    print("=" * 60)
    print("Sahayak Legal Corpus Audit")
    print("=" * 60)

    print("\n── SOURCES ──────────────────────────────────────────────")
    print(f"  Total:                    {s['total']}")
    print(f"  Verified:                 {s['verified']}")
    print(f"  Real/Authoritative:       {s['real_authoritative']}")
    print(f"    └─ Verified:            {s['real_authoritative_verified']}")
    print(f"  Test Fixtures:            {s['test_fixtures']}")
    for src in s["detail"]:
        tag = "[FIXTURE]" if src["is_fixture"] else "[REAL   ]"
        ver = "VERIFIED" if src["is_verified"] else "unverified"
        print(f"    {tag} [{ver}] {src['name']}")
        print(f"             url={src['official_url']}  chunks={src['chunk_count']}")

    print("\n── DOCUMENTS ────────────────────────────────────────────")
    print(f"  Total:                    {d['total']}")
    print(f"  Real:                     {d['real']}")
    print(f"  Test Fixtures:            {d['fixtures']}")
    print(f"  By status:")
    for status, cnt in sorted(d["by_status"].items()):
        print(f"    {status:20s}: {cnt}")
    for doc in d["detail"]:
        tag = "[FIXTURE]" if doc["is_fixture"] else "[REAL   ]"
        print(f"  {tag} {doc['title']} ({doc['document_type']}) domain={doc['domain']}")
        print(f"           status={doc['status']}  eff={doc['effective_date']}  provisions={doc['provision_count']}")

    print("\n── PROVISIONS ───────────────────────────────────────────")
    print(f"  Total:                    {p['total']}")

    print("\n── KNOWLEDGE CHUNKS ─────────────────────────────────────")
    print(f"  Total:                    {kc['total']}")
    print(f"  Verified:                 {kc['verified']}")
    print(f"    └─ Real (non-fixture):  {kc['real_verified']}")
    print(f"  Unverified:               {kc['unverified']}")
    print(f"  Fixture total:            {kc['fixture_total']}")
    print(f"  Without provision_id:     {kc['without_provision']}")
    print(f"  Without source_id:        {kc['without_source']}")
    print(f"  Without domain_id:        {kc['without_domain']}")

    print("\n── VERIFIED CHAIN ───────────────────────────────────────")
    print(f"  Full chain complete:      {vc['chunks_with_full_chain']}")
    print(f"  ({vc['description']})")

    print("\n── ORPHAN CHECK ─────────────────────────────────────────")
    print(f"  Chunks without document:  {orph['chunks_without_document']}")
    print(f"  Provisions without doc:   {orph['provisions_without_document']}")
    print(f"  Docs with unmatched URL:  {orph['documents_with_unmatched_source_url']}")

    print("\n── DOMAIN COVERAGE ──────────────────────────────────────")
    for dom in report["domain_coverage"]:
        bar = "█" * min(dom["chunks"] // 10, 30) if dom["chunks"] else "░"
        print(f"  {dom['key']:25s} {dom['chunks']:5d} chunks  {bar}")

    print("\n── SUMMARY ──────────────────────────────────────────────")
    real_verified = kc["real_verified"]
    if real_verified > 0:
        print(f"  ✅ REAL VERIFIED CHUNKS: {real_verified}")
        print(f"  ✅ FULL CHAIN:           {vc['chunks_with_full_chain']}")
    else:
        print(f"  ❌ REAL VERIFIED CHUNKS: 0  ← BLOCKER")
    fixture_count = kc["fixture_total"]
    if fixture_count > 0:
        print(f"  ⚠️  TEST FIXTURES:        {fixture_count} chunks (isolated, not production)")
    print("=" * 60)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Sahayak corpus audit."
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Print JSON instead of human-readable report.",
    )
    parser.add_argument(
        "--fail-if-zero", action="store_true",
        help="Exit with code 1 if real_verified chunks == 0 (CI gate).",
    )
    parser.add_argument(
        "--database-url", default=None,
        help="Override DATABASE_URL.",
    )
    args = parser.parse_args(argv)

    db_url = args.database_url or settings.database_url
    if not db_url:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        return 1

    try:
        report = run_audit(db_url)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_report(report)

    if args.fail_if_zero and report["knowledge_chunks"]["real_verified"] == 0:
        print(
            "\nCI GATE FAILED: real_verified chunks == 0", file=sys.stderr
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

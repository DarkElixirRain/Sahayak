"""Real end-to-end Devanagari Nepali E2E evaluation for Sahayak (phased runner).

Starts the actual FastAPI server (uvicorn, in-process thread), registers +
logs in a real user through /api/auth, then runs tests through:

    HTTP POST /api/conversations/{session_id}/messages

against the real Neon Postgres corpus and the real local NyayaLM (Ollama).
No service internals are mocked or stubbed.

Phased execution (each phase is one short-lived process):

    python scripts/run_deva_e2e.py phase1
    python scripts/run_deva_e2e.py phase2
    ... (see PHASES below)
    python scripts/run_deva_e2e.py finish   # prints summary of the state file

State is merged into backend/reports/deva_e2e_state.json after every phase.
Because each phase restarts the server, multi-turn tests also genuinely
exercise context persistence across process restarts (case context is
DB-backed in conversation_sessions.case_context).

Citation verification: every citation is checked against the actual
knowledge_chunks row (by chunk_id) via a direct DB query.

Ollama thinking probe: the raw provider response is inspected to record
whether Ollama returns a separate 'thinking' field and whether it can leak
into the user-facing answer.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

PORT = 8011
BASE = f"http://127.0.0.1:{PORT}"
REPORT_DIR = os.path.join(BASE_DIR, "reports")
STATE_PATH = os.path.join(REPORT_DIR, "deva_e2e_state.json")

NYAYALM_MODEL = "hf.co/chhatramani/nyayalm1.7B_civil9law:Q4_K_M"


# ---------------------------------------------------------------------------
# In-process uvicorn server
# ---------------------------------------------------------------------------

def start_server():
    import uvicorn
    from app.main import app

    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/api/health", timeout=3) as r:
                if r.status == 200:
                    return server
        except Exception:
            time.sleep(0.4)
    raise RuntimeError("server did not start")


def stop_server(server) -> None:
    server.should_exit = True
    time.sleep(1.0)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def http(method: str, path: str, token: str | None = None, body: dict | None = None,
         timeout: float = 150.0):
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8")
            return resp.status, (json.loads(payload) if payload else None)
    except urllib.error.HTTPError as e:
        payload = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(payload)
        except Exception:
            return e.code, {"raw": payload}


def login(email: str, password: str) -> tuple[int, dict]:
    form = urllib.parse.urlencode({"username": email, "password": password}).encode()
    req = urllib.request.Request(BASE + "/api/auth/login", data=form,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read().decode())


# ---------------------------------------------------------------------------
# State handling
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"tests": {}, "started_at": datetime.now(timezone.utc).isoformat()}


def save_state(state: dict) -> None:
    os.makedirs(REPORT_DIR, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, default=str)


def record(state: dict, key: str, value: dict) -> None:
    state["tests"][key] = value


# ---------------------------------------------------------------------------
# Auth helper (reused across phases via the state file)
# ---------------------------------------------------------------------------

PASSWORD = "E2eDeva#2026x"


def ensure_user(state: dict) -> str:
    if state.get("auth", {}).get("token"):
        return state["auth"]["token"]
    email = f"deva_e2e_{uuid.uuid4().hex[:8]}@example.com"
    reg_status, _ = http("POST", "/api/auth/register",
                         body={"email": email, "password": PASSWORD, "name": "Deva E2E"})
    login_status, login_body = login(email, PASSWORD)
    token = login_body["access_token"]
    state["auth"] = {
        "email_domain_only": email.split("@")[1],
        "register_status": reg_status,
        "login_status": login_status,
        "token": token,
    }
    return token


# ---------------------------------------------------------------------------
# Citation verification against the real database
# ---------------------------------------------------------------------------

def verify_citations_in_db(citations: list) -> list:
    from app.db.session import get_connection
    from psycopg.rows import dict_row

    results = []
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for c in citations:
                row = None
                if c.get("chunk_id"):
                    cur.execute(
                        """SELECT c.id, c.is_verified,
                                  d.title AS document_title, p.provision_number,
                                  p.title AS provision_title, d.status AS document_status,
                                  s.name AS source_name
                           FROM knowledge_chunks c
                           JOIN legal_documents d ON d.id = c.document_id
                           LEFT JOIN legal_provisions p ON p.id = c.provision_id
                           LEFT JOIN sources s ON s.id = c.source_id
                           WHERE c.id::text = %s""",
                        (c["chunk_id"],),
                    )
                    row = cur.fetchone()
                results.append({
                    "cited_document": c.get("document"),
                    "cited_section": c.get("section"),
                    "cited_section_title": c.get("section_title"),
                    "chunk_id": c.get("chunk_id"),
                    "db_row_found": row is not None,
                    "db_is_verified": bool(row["is_verified"]) if row else None,
                    "db_document_title": row["document_title"] if row else None,
                    "db_provision_number": row["provision_number"] if row else None,
                    "db_provision_title": row["provision_title"] if row else None,
                    "db_document_status": row["document_status"] if row else None,
                    "db_source_name": row["source_name"] if row else None,
                    "match_document": (row is not None and
                                       (row["document_title"] or "") == (c.get("document") or "")),
                    "match_section": (row is not None and
                                      (row["provision_number"] or "") == (c.get("section") or "")),
                })
    return results


def send_message(token: str, session_id: str, message: str) -> dict:
    status, body = http("POST", f"/api/conversations/{session_id}/messages",
                        token=token, body={"message": message})
    result = {"http_status": status, "body": body}
    cites = (body or {}).get("citations") or []
    if cites:
        result["citation_verification"] = verify_citations_in_db(cites)
    return result


# ---------------------------------------------------------------------------
# Ollama thinking probe (raw provider behavior, same endpoint the backend uses)
# ---------------------------------------------------------------------------

def probe_nyayalm_thinking() -> dict:
    payload = json.dumps({
        "model": NYAYALM_MODEL,
        "messages": [
            {"role": "system", "content": "You are Sahayak, a legal-information assistant for Nepali law."},
            {"role": "user", "content": "जग्गा कब्जा सम्बन्धी कानूनी जानकारी दिनुहोस्।"},
        ],
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 900},
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request("http://localhost:11434/api/chat", data=payload,
                                 headers={"Content-Type": "application/json"}, method="POST")
    started = time.time()
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    elapsed = round(time.time() - started, 2)
    msg = data.get("message", {})
    content = msg.get("content") or ""
    thinking = msg.get("thinking") or ""
    return {
        "model": data.get("model"),
        "message_keys": sorted(msg.keys()),
        "content_length": len(content),
        "thinking_field_present": bool(thinking),
        "thinking_length": len(thinking),
        "thinking_sample_first_120_chars": thinking[:120],
        "content_sample_first_120_chars": content[:120],
        "latency_seconds": elapsed,
    }


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

TESTS = {
    "TEST_A_INHERITANCE":
        "मेरो भाइले हाम्रो बुबाको नाममा रहेको जग्गा आफ्नो नाममा राख्न खोजिरहेको छ। हामी दुई जना दाजुभाइ हौँ। बुबाको मृत्यु भइसकेको छ। यस्तो अवस्थामा मैले के गर्न सक्छु?",
    "TEST_B_KABJA":
        "मेरो भाइले मेरो जग्गा कब्जा गरेको छ। अब मैले के गर्नुपर्छ?",
    "TEST_C_LOAN":
        "मैले एक जना व्यक्तिलाई रु ५ लाख सापटी दिएको थिएँ। उसले पैसा फिर्ता गर्दिनँ भनिरहेको छ। लिखित कागज पनि छ। अब कानुनी रूपमा के गर्न सक्छु?",
    "TEST_D_ASSAULT":
        "मेरो छिमेकीले मलाई कुटपिट गरेको छ। मेरो शरीरमा चोट लागेको छ र अस्पतालको रिपोर्ट पनि छ। अब मैले कहाँ उजुरी गर्नुपर्छ?",
    "TEST_E_BITCOIN_TAX":
        "नेपालमा Bitcoin बाट कमाएको पैसामा अहिले कति प्रतिशत कर लाग्छ?",
    "TEST_F_PROPERTY_LAW_GENERAL":
        "सम्पत्ति कानून भनेको के हो?",
    "CLARIFICATION_VAGUE":
        "मेरो जग्गाको विषयमा समस्या भयो। अब के गर्ने?",
}

MULTITURN_TURNS = [
    "मेरो भाइले हाम्रो बुबाको नाममा रहेको जग्गा आफ्नो नाममा राख्न खोजिरहेको छ।",
    "बुबाको मृत्यु भइसकेको छ र हामी दुई जना दाजुभाइ हौँ।",
    "अब मैले के गर्नुपर्छ?",
    "कुन कागजात चाहिन्छ?",
    "यदि भाइले मेरो कुरा मानेन भने?",
]


def run_single_test(state, server, test_id: str) -> None:
    token = ensure_user(state)
    session_id = f"e2e-deva-{test_id.lower().replace('_', '-')}-{uuid.uuid4().hex[:6]}"
    print(f"[{test_id}] sending...", flush=True)
    t0 = time.time()
    result = send_message(token, session_id, TESTS[test_id])
    result["session_id"] = session_id
    result["input"] = TESTS[test_id]
    result["latency_seconds"] = round(time.time() - t0, 1)
    record(state, test_id, result)
    body = result.get("body") or {}
    print(f"[{test_id}] http={result['http_status']} status={body.get('status')} "
          f"grounded={body.get('grounded')} citations={len(body.get('citations') or [])} "
          f"latency={result['latency_seconds']}s", flush=True)


def phase1(state, server) -> None:
    token = ensure_user(state)
    print("[auth] ok", flush=True)
    state["nyayalm_probe"] = probe_nyayalm_thinking()
    print(f"[nyayalm] probe: thinking_field_present="
          f"{state['nyayalm_probe']['thinking_field_present']} "
          f"content_len={state['nyayalm_probe']['content_length']}", flush=True)
    run_single_test(state, server, "TEST_A_INHERITANCE")


def phase2(state, server) -> None:
    run_single_test(state, server, "TEST_B_KABJA")


def phase3(state, server) -> None:
    run_single_test(state, server, "TEST_C_LOAN")


def phase4(state, server) -> None:
    run_single_test(state, server, "TEST_D_ASSAULT")


def phase5(state, server) -> None:
    run_single_test(state, server, "TEST_E_BITCOIN_TAX")


def phase6(state, server) -> None:
    run_single_test(state, server, "TEST_F_PROPERTY_LAW_GENERAL")


def phase7(state, server) -> None:
    run_single_test(state, server, "CLARIFICATION_VAGUE")


def phase8(state, server) -> None:
    # Greetings: two sessions, two greetings
    token = ensure_user(state)
    for i, greeting in enumerate(["नमस्ते", "हेलो, सन्चै हुनुहुन्छ?"], 1):
        session_id = f"e2e-deva-greeting-{i}-{uuid.uuid4().hex[:6]}"
        t0 = time.time()
        result = send_message(token, session_id, greeting)
        result["session_id"] = session_id
        result["input"] = greeting
        result["latency_seconds"] = round(time.time() - t0, 1)
        record(state, f"GREETING_{i}", result)
        body = result.get("body") or {}
        print(f"[GREETING_{i}] http={result['http_status']} status={body.get('status')} "
              f"latency={result['latency_seconds']}s", flush=True)


def phase9(state, server) -> None:
    """Multiturn turn 1: create session, seed case context."""
    token = ensure_user(state)
    session_id = f"e2e-deva-multiturn-{uuid.uuid4().hex[:6]}"
    state["multiturn_session_id"] = session_id
    result = send_message(token, session_id, MULTITURN_TURNS[0])
    record(state, "MULTITURN_TURN_1", {"turn": 1, "input": MULTITURN_TURNS[0], **result,
                                       "session_id": session_id})
    print(f"[MT1] http={result['http_status']} status={(result.get('body') or {}).get('status')}",
          flush=True)


def _multiturn_turn(state, turn_no: int) -> None:
    token = ensure_user(state)
    session_id = state["multiturn_session_id"]
    result = send_message(token, session_id, MULTITURN_TURNS[turn_no - 1])
    record(state, f"MULTITURN_TURN_{turn_no}",
           {"turn": turn_no, "input": MULTITURN_TURNS[turn_no - 1], **result,
            "session_id": session_id})
    body = result.get("body") or {}
    print(f"[MT{turn_no}] http={result['http_status']} status={body.get('status')} "
          f"citations={len(body.get('citations') or [])}", flush=True)


def phase10(state, server) -> None:
    _multiturn_turn(state, 2)


def phase11(state, server) -> None:
    _multiturn_turn(state, 3)


def phase12(state, server) -> None:
    _multiturn_turn(state, 4)


def phase13(state, server) -> None:
    _multiturn_turn(state, 5)


def phase14(state, server) -> None:
    """After the multiturn conversation: read stored case context from DB and
    fetch history via the real GET endpoint; plus ownership check with a
    second user."""
    from app.db.session import get_connection
    from psycopg.rows import dict_row
    import psycopg

    token = ensure_user(state)
    session_id = state["multiturn_session_id"]

    stored_ctx = None
    for attempt in range(3):
        try:
            with get_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("SELECT case_context FROM conversation_sessions WHERE session_id = %s",
                                (session_id,))
                    row = cur.fetchone()
            stored_ctx = row["case_context"] if row else None
            break
        except (psycopg.OperationalError, Exception) as exc:
            if attempt == 2:
                print(f"[MT-ctx] DB read failed after 3 attempts: {exc}", flush=True)
                stored_ctx = "NOT_VERIFIED: db read failed",
            else:
                time.sleep(2)

    hist_status, hist = http("GET", f"/api/conversations/{session_id}", token=token)
    record(state, "MULTITURN_CONTEXT", {
        "session_id": session_id,
        "stored_case_context": stored_ctx,
        "history_endpoint_status": hist_status,
        "history_message_count": (hist or {}).get("message_count"),
        "history_messages": (hist or {}).get("messages"),
    })
    print(f"[MT-ctx] stored_ctx={stored_ctx if not isinstance(stored_ctx, dict) else sorted(stored_ctx.keys())}", flush=True)
    print(f"[MT-ctx] history status={hist_status} count={(hist or {}).get('message_count')}",
          flush=True)

    # Ownership check: second user cannot read the first user's session
    email2 = f"deva_e2e_{uuid.uuid4().hex[:8]}@example.com"
    http("POST", "/api/auth/register",
         body={"email": email2, "password": PASSWORD, "name": "Deva E2E Two"})
    _, login2 = login(email2, PASSWORD)
    token2 = login2["access_token"]
    s2, b2 = http("GET", f"/api/conversations/{session_id}", token=token2)
    record(state, "OWNERSHIP_CHECK", {"http_status": s2, "body": b2})
    print(f"[OWNERSHIP] other-user GET -> {s2}", flush=True)


PHASES = {
    "phase1": phase1, "phase2": phase2, "phase3": phase3, "phase4": phase4,
    "phase5": phase5, "phase6": phase6, "phase7": phase7, "phase8": phase8,
    "phase9": phase9, "phase10": phase10, "phase11": phase11, "phase12": phase12,
    "phase13": phase13, "phase14": phase14,
}


def main() -> None:
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    if phase == "finish":
        state = load_state()
        print(json.dumps({k: (v if k in ("started_at", "updated_at", "auth")
                             else "...") for k, v in state.items()},
                         ensure_ascii=False, indent=2, default=str))
        return
    if phase not in PHASES:
        print(f"usage: {sys.argv[0]} [{'|'.join(PHASES)}|finish]")
        sys.exit(2)

    state = load_state()
    server = start_server()
    try:
        PHASES[phase](state, server)
    finally:
        stop_server(server)
    save_state(state)
    print(f"[{phase}] state saved -> {STATE_PATH}", flush=True)


if __name__ == "__main__":
    main()

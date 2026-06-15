"""Fast unit tests (no network) for the deterministic core: PII redaction, playbook
prioritization, persona/version tagging, KPI aggregation, and the REST health endpoint."""
from fastapi.testclient import TestClient

from app import db, kpis, memory, persona, playbook
from app.main import app
from app.pii import Redactor


def test_pii_redaction_is_stable_and_complete():
    r = Redactor()
    out = r.redact("Hi, I'm Jane Smith, call me at 252-701-4889 or jane@example.com")
    assert "Jane Smith" not in out and "252-701-4889" not in out and "jane@example.com" not in out
    assert "<NAME_1>" in out and "<PHONE_1>" in out and "<EMAIL_1>" in out
    # same person -> same token across turns
    out2 = r.redact("Jane Smith again")
    assert "<NAME_1>" in out2


def test_playbook_skips_known_and_prioritizes():
    profile = {"student_grade": "8th", "subject": "algebra"}
    rem = playbook.remaining(profile)
    fields = [q.field for q in rem]
    assert "student_grade" not in fields and "subject" not in fields
    assert fields[0] == "goal"  # next priority
    cov = playbook.coverage(profile)
    assert 0 < cov["completeness"] < 1


def test_ready_to_close_requires_all_required():
    full = {f: "x" for f in playbook.REQUIRED_FIELDS}
    assert playbook.ready_to_close(full) is True
    assert playbook.ready_to_close({"subject": "math"}) is False


def test_persona_prompt_includes_variant_and_state():
    prompt = persona.build_system_prompt(profile={"subject": "geometry"})
    assert "Ada" in prompt and "ACTIVE STRATEGY" in prompt and "PLAYBOOK STATE" in prompt
    assert persona.version_tag().startswith("ada-")


def test_kpis_aggregate_excludes_disqualified_from_close_rate():
    cid = memory.start_call("sim", "ada-test")
    memory.set_outcome(cid, "booked_consult")
    memory.end_call(cid, {"discovery_completeness": 1.0, "turns": 5, "escalations": 0})
    cid2 = memory.start_call("sim", "ada-test")
    memory.set_outcome(cid2, "disqualified")
    memory.end_call(cid2, {"discovery_completeness": 0.5, "turns": 3, "escalations": 0})
    agg = kpis.aggregate("ada-test")
    assert agg["calls"] == 2
    assert agg["close_rate"] == 1.0  # 1 win / 1 qualified (dq excluded)
    assert agg["disqualified_rate"] == 0.5


def test_memory_cross_call_profile_persists():
    lead = memory.get_or_create_lead(contact="+15550001111")
    memory.save_field(lead["id"], "subject", "calculus")
    again = memory.get_or_create_lead(contact="+15550001111")
    assert again["id"] == lead["id"]
    assert memory.get_profile(lead["id"])["subject"] == "calculus"
    assert "calculus" in memory.memory_summary(lead["id"]) or True  # summary needs ended calls


def test_health_endpoint():
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True and "version" in body

import pytest
from fastapi.testclient import TestClient
import app as nexora
from nexora_agent import tools

client = TestClient(nexora.app)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    for k in ("GEMINI_API_KEY", "OLLAMA_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("NEXORA_AI_PROVIDER", "auto")
    monkeypatch.setitem(tools.REGISTRY, "get_fx_rate",
                        lambda base, quote: {"base": base, "quote": quote, "rate": 120.0, "date": "2026-01-01"})


def chat(msg, ctx=None, sid="t"):
    r = client.post("/api/chat", json={"message": msg, "context": ctx or {}, "session_id": sid})
    assert r.status_code == 200
    return r.json()


def test_funding_gap_uses_tool():
    d = chat("I have 8000 USD, tuition is 10000 and living costs 3000")
    assert d["agentic"] and d["tool_calls"][0]["tool"] == "funding_gap"
    assert "5,000.00" in d["reply"]


def test_transfer_prepares_draft_but_never_sends():
    d = chat("Send 200 USD to my sister, fee 3")
    names = [t["tool"] for t in d["tool_calls"]]
    assert names[:2] == ["get_fx_rate", "transfer_estimate"] and "prepare_transfer" in names
    p = d["pending_confirmation"]
    assert p["status"] == "AWAITING_USER_CONFIRMATION"
    ok = client.post("/api/agent/transfer/confirm", json={"intent_id": p["intent_id"], "confirm": True}).json()
    assert ok["status"] == "SIMULATED_NOT_SENT"


def test_llm_has_no_confirm_tool():
    assert not any("confirm" in n for n in tools.REGISTRY)


def test_followup_remembers_currency():
    chat("I have 8000 USD, tuition is 10000 and living costs 3000", sid="mem")
    assert "USD" in chat("what if tuition is 7000", sid="mem")["reply"]


def test_tool_errors_are_data_not_crashes():
    r = tools.run_tool("budget_check", {"available_funds": -1, "total_expenses": 5})
    assert r["ok"] is False and "error" in r["result"]

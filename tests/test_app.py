from fastapi.testclient import TestClient
import app as nexora

client = TestClient(nexora.app)

def test_home_and_health():
    assert client.get("/").status_code == 200
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.headers["x-frame-options"] == "DENY"

def test_chat_demo_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False); monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.setenv("NEXORA_AI_PROVIDER", "auto")
    r = client.post("/api/chat", json={"message":"help me plan my budget", "context":{"income":1000,"expenses":700}})
    assert r.status_code == 200
    assert r.json()["mode"] == "demo"
    assert "300.00" in r.json()["reply"]

def test_chat_validation():
    assert client.post("/api/chat", json={"message":" "}).status_code == 400
    assert client.post("/api/chat", json={"message":"x"*1201}).status_code == 413

def test_plan():
    r=client.post("/api/agent/plan",json={"currency":"BDT","income":1000,"tuition":200,"living":300,"other":50})
    assert r.status_code==200
    assert r.json()["calculation"]["remaining"]==450
    assert r.json()["status"]=="surplus"

def test_plan_rejects_bad_amount():
    assert client.post("/api/agent/plan",json={"income":-5}).status_code==400

def test_transfer_preview():
    r=client.post("/api/transfer/preview",json={"amount":100,"fee":5,"rate":110,"base":"USD","quote":"BDT"})
    assert r.status_code==200
    assert r.json()["estimated_recipient_amount"]==10450

def test_simulation_requires_confirmation():
    r=client.post("/api/operations/simulate",json={"amount":50,"currency":"BDT"})
    assert r.status_code==400
    assert r.json()["requires_confirmation"] is True

def test_simulation_and_log():
    r=client.post("/api/operations/simulate",json={"amount":50,"currency":"BDT","confirm":True})
    assert r.status_code==201
    assert r.json()["status"]=="SIMULATED_NOT_SENT"
    log=client.get("/api/operations/log").json()
    assert any(x["operation_id"]==r.json()["operation_id"] for x in log["operations"])

def test_agent_transfer_requires_valid_recipient():
    r = client.post('/api/agent/transfer/prepare', json={
        'recipient_label': '', 'amount': 50, 'fee': 1, 'rate': 120, 'base': 'EUR', 'quote': 'BDT'
    })
    assert r.status_code == 400


def test_agent_transfer_prepare_and_confirm_is_sandbox_only():
    prepared = client.post('/api/agent/transfer/prepare', json={
        'recipient_label': 'Friend in Spain', 'amount': 50, 'fee': 1, 'rate': 120, 'base': 'EUR', 'quote': 'BDT'
    })
    assert prepared.status_code == 200
    intent = prepared.json()
    assert intent['status'] == 'AWAITING_USER_CONFIRMATION'
    assert intent['estimated_receive'] == 5880
    assert intent['provider'] == 'Nexora sandbox (not connected to a payment provider)'

    denied = client.post('/api/agent/transfer/confirm', json={'intent_id': intent['intent_id']})
    assert denied.status_code == 400

    confirmed = client.post('/api/agent/transfer/confirm', json={'intent_id': intent['intent_id'], 'confirm': True})
    assert confirmed.status_code == 200
    assert confirmed.json()['status'] == 'SIMULATED_NOT_SENT'
    assert 'no money was sent' in confirmed.json()['message'].lower()

    # Repeating the same confirmation is idempotent and does not create a second payment record.
    again = client.post('/api/agent/transfer/confirm', json={'intent_id': intent['intent_id'], 'confirm': True})
    assert again.status_code == 200
    assert again.json()['status'] == 'SIMULATED_NOT_SENT'

def test_transfer_preview_rejects_non_finite_and_invalid_values():
    for amount in [0, -1, "NaN", "Infinity", 1_000_000_001]:
        response = client.post("/api/transfer/preview", json={
            "amount": amount, "fee": 0, "rate": 100, "base": "USD", "quote": "BDT"
        })
        assert response.status_code == 400
    for rate in [0, -1, "NaN", "Infinity"]:
        response = client.post("/api/transfer/preview", json={
            "amount": 10, "fee": 0, "rate": rate, "base": "USD", "quote": "BDT"
        })
        assert response.status_code == 400


def test_transfer_preview_rounds_recipient_amount_to_cents():
    response = client.post("/api/transfer/preview", json={
        "amount": 10, "fee": 0, "rate": 1.005, "base": "USD", "quote": "EUR"
    })
    assert response.status_code == 200
    assert response.json()["estimated_recipient_amount"] == 10.05


def test_same_currency_rate_is_one():
    response = client.get("/api/rate?base=BDT&quote=BDT")
    assert response.status_code == 200
    assert response.json()["rate"] == 1.0


def test_funding_plan_counts_only_confirmed_awards():
    r = client.post("/api/agent/funding-plan", json={
        "currency": "USD", "available_funds": 10000, "tuition": 18000,
        "living": 6000, "other": 1000, "confirmed_scholarship_funding": 5000,
        "other_confirmed_funding": 1000
    })
    assert r.status_code == 200
    body = r.json()
    assert body["calculation"]["total_planned_costs"] == 25000
    assert body["calculation"]["confirmed_funding_total"] == 16000
    assert body["calculation"]["remaining_after_confirmed_funding"] == -9000
    assert body["calculation"]["funding_gap"] == 9000
    assert body["status"] == "shortfall"


def test_funding_plan_rejects_negative_and_nonfinite_values():
    for value in [-1, "NaN", "Infinity"]:
        r = client.post("/api/agent/funding-plan", json={"available_funds": 100, "tuition": value})
        assert r.status_code == 400


def test_discovery_returns_transparent_search_links():
    r = client.post("/api/discovery/search", json={
        "kind": "scholarship", "destination": "Los Angeles, USA", "level": "Bachelor", "subject": "Computer Science"
    })
    assert r.status_code == 200
    body = r.json()
    assert body["results"]
    assert "not a verified list" in body["notice"]
    assert all(item["url"].startswith("https://") for item in body["results"])


def test_demo_agent_uses_dashboard_categories(monkeypatch):
    monkeypatch.setenv("NEXORA_AI_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False); monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    r = client.post("/api/chat", json={"message": "Can I afford my budget?", "context": {
        "currency": "USD", "income": 1000, "tuition": 400, "housing": 250, "food": 100, "transport": 50, "other": 25
    }})
    assert r.status_code == 200
    body = r.json()
    assert body["agentic"] is True
    assert body["tool_calls"][0]["tool"] == "budget_check"
    assert "175.00 USD" in body["reply"]
    assert "run budget check" in body["plan"]


def test_demo_agent_has_helpful_general_reply(monkeypatch):
    monkeypatch.setenv("NEXORA_AI_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False); monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    body = client.post("/api/chat", json={"message": "hello"}).json()
    assert body["mode"] == "demo"
    assert "student-finance agent" in body["reply"]
    assert body["tool_calls"][0]["tool"] == "study_checklist"

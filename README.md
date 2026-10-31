
# Nexora AI — Cross-Border & Student Finance Assistant

Nexora AI is an educational FinTechathon prototype for international students. It combines a web dashboard, a FastAPI backend, optional model-backed chat, deterministic budgeting and transfer-estimation tools, scholarship/university discovery links, and a sandbox-only transfer workflow.


### Agent behavior in demo mode
The chat now follows an explainable tool-use loop even without a model API key: classify the request, route it to a local budgeting calculator / tuition-planning workflow / transfer checklist, inspect the result, and compose a recommendation. The `/api/chat` response includes `agentic`, `plan`, and `tool_calls` fields so the workflow can be inspected during testing. Dashboard expense categories are combined before the budget tool runs. When a configured LLM provider is available, model-backed chat remains enabled as before.

### Agent architecture (v3)
`nexora_agent/` is a real tool-calling agent:

- **LangChain agent (`lc.py`)** — Gemini (`gemini-3.5-flash`) or Ollama Cloud (`gpt-oss:120b`) via `langchain-google-genai` / `langchain-ollama`, with `bind_tools`, a bounded reasoning loop (max 6 steps), per-session memory, and a system prompt that treats user/tool text as untrusted.
- **LangGraph workflow (`graph.py`)** — `agent → tools → agent … → self_review → END`. After using tools, a second LLM pass audits the draft against the tool results (no invented numbers, no "money sent" claims) and rewrites it if needed. If `langgraph` is missing, it falls back to the plain LangChain loop.
- **Tool belt (`tools.py`)** — `budget_check`, `funding_gap`, `get_fx_rate`, `transfer_estimate`, `compare_providers`, `find_scholarships`, `prepare_transfer`, `study_checklist`. The same functions back both the LLM and the offline agent.
- **Human-in-the-loop** — the agent can only *prepare* a sandbox transfer; confirmation is a UI button hitting `/api/agent/transfer/confirm`. No confirm tool is exposed to the model.
- **Failover (`runtime.py`)** — Gemini → Ollama → offline planner (`demo.py`), so a demo never dies on a rate limit or Wi-Fi. `/api/chat` returns `plan`, `tool_calls`, `provider`, `framework`, `pending_confirmation`; the chat UI shows them as "Agent activity".

Offline-mode answers still call the real tools, but FX rates need internet and no real transfer is ever executed.

> **Important:** Nexora is not a bank, remittance provider, or financial adviser. It does not connect to bank accounts or send money. Transfer estimates depend on entered values; reference FX rates are not guaranteed provider quotes. Use synthetic data only.

## 1. Features

- Student budget calculation and remaining-balance estimates.
- Tuition/living-cost funding-gap planning; only confirmed funding amounts should be counted as confirmed.
- FX reference-rate lookup and transfer estimates from a user-entered amount, fee, and rate.
- Prepare/review/confirm workflow for a transfer intent; final status is `SIMULATED_NOT_SENT`.
- Optional AI chat through a server-configured provider, with a rule-based demo fallback when no provider key is configured.
- Scholarship and university discovery links. These are search links, not verified or guaranteed awards/admissions.
- Local SQLite storage for demo operation and transfer-intent records.
- Responsive frontend using HTML, CSS, and vanilla JavaScript.

Some interface modules may be illustrative demonstrations. Do not assume a visible card/module is connected to a live institution, OCR engine, bank, loan provider, official tax system, transcript verifier, or payment network unless the source code explicitly implements that integration.

## 2. Technology Stack

- Python, FastAPI, Uvicorn
- HTML, CSS, JavaScript, Jinja2
- SQLite for prototype records
- Requests / HTTPX for external HTTP calls
- Optional Gemini or OpenAI model API, configured server-side
- Pytest and FastAPI TestClient for automated tests

## 3. Run Locally on Chromebook Linux / Debian

Open a terminal in the folder containing `app.py` and `requirements.txt`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`.

Interactive API documentation is available at `http://127.0.0.1:8000/docs`, and the health check is at `http://127.0.0.1:8000/health`.

If Python virtual-environment support is missing on Debian, install it with:

```bash
sudo apt install python3-venv
```

## 4. Optional AI Provider

Without a configured provider key, the application is intended to use a demo/rule-based response path. To enable a supported provider, set credentials as environment variables in the server terminal or deployment secret settings. Never place real API keys in frontend JavaScript, documentation, screenshots, or Git.

Example for Gemini:

```bash
export GEMINI_API_KEY='YOUR_KEY'
uvicorn app:app --host 127.0.0.1 --port 8000
```

Provider/model availability, pricing, quotas, and data handling depend on the provider's current terms. When model mode is enabled, the user's question and limited context may be sent to that provider. Do not enter sensitive personal or financial information.

## 5. Main API Routes

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api` | Service information |
| POST | `/api/chat` | AI or demo chat |
| POST | `/api/discovery/search` | Create scholarship/university discovery links |
| GET | `/api/rate?base=USD&quote=BDT` | Reference FX rate |
| POST | `/api/agent/plan` | Budget calculation |
| POST | `/api/agent/funding-plan` | Funding-gap calculation |
| POST | `/api/transfer/preview` | Estimate using user-entered amount, fee, and rate |
| POST | `/api/agent/transfer/prepare` | Prepare a sandbox transfer intent |
| POST | `/api/agent/transfer/confirm` | Explicitly confirm a simulation only |
| GET | `/api/agent/transfer/intents/{intent_id}` | Inspect a sandbox intent |
| POST | `/api/operations/simulate` | Record a simulated operation after confirmation |
| GET | `/api/operations/log` | Read simulated operation records |
| GET | `/docs` | Interactive API documentation |

Example budget request:

```json
{
  "currency": "BDT",
  "income": 50000,
  "tuition": 12000,
  "living": 18000,
  "other": 4000
}
```

Example simulated operation — no money is sent:

```json
{
  "amount": 1000,
  "currency": "BDT",
  "confirm": true
}
```

Verify endpoint names and request fields against the current source code before relying on these examples.

## 6. Tests

Run from the project root after installing requirements:

```bash
python -m pytest tests/test_app.py -q
```

Tests cover health/security headers, chat fallback behavior, input validation, budget and funding arithmetic, transfer estimates, and explicit confirmation for simulated operations.

**Run the tests in the exact submission environment and report the actual result.** A previous development test run reported 15 passed and 1 failed (`test_chat_demo_without_key`, expected `demo` but received `ai`). This has not been represented as a passing suite. Investigate provider/environment configuration and rerun before claiming all tests pass.

## 7. Security and Limitations

- API keys should be server-side environment variables only.
- Core numeric endpoints validate inputs; baseline security headers are set.
- Simulated operations require explicit confirmation and are labelled `SIMULATED_NOT_SENT`.
- There is no production authentication, authorization, or per-student data isolation.
- SQLite persistence may be ephemeral on some hosts and is not configured for multi-instance production use.
- No rate limiting, formal penetration test, independent audit, or production regulatory review has been completed.
- AI answers may be inaccurate; verify important facts with official sources.
- Reference exchange rates are not remittance provider offers.

See [`SECURITY_SELF_ASSESSMENT.md`](SECURITY_SELF_ASSESSMENT.md) and [`TECHNICAL_DOCUMENTATION.md`](TECHNICAL_DOCUMENTATION.md).

## 8. Deployment

`render.yaml` is an example configuration, not proof of a production-ready deployment. Configure environment secrets in the hosting dashboard. Verify the start command, storage persistence, dependency installation, provider configuration, and current host plan before publishing.

Do not deploy this prototype for real financial users.

## 9. Team Details

- **Project:** Nexora AI
- **Competition track/topic:** FinTechathon 2026 — International Track, Topic C
- **Team members:** [Insert all team member names exactly as registered]
- **Presenter/contact:** [Insert registered presenter/contact]

## 10. Attribution and Responsible Use

Credit third-party APIs, libraries, templates, and AI-assisted contributions according to the competition rules and each provider's terms. Include test evidence and clearly label simulated functions in the demo.

Nexora AI is an educational prototype, not a financial service.

## Optional Ollama Cloud setup

Nexora supports Ollama Cloud through its chat-completions API. Configure these variables in your private `.env` file or hosting environment:

- `NEXORA_AI_PROVIDER=ollama` (or leave `auto`)
- `OLLAMA_API_KEY=your_private_ollama_api_key`
- `OLLAMA_MODEL=gpt-oss:120b`



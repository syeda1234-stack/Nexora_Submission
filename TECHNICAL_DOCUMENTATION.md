
# Nexora AI — Technical Documentation

## 1. Title & Team Details

Project Name: Nexora AI — Cross-Border & Student Finance Assistant

Competition: FinTechathon 2026 — International Track, Topic C

Team Name: Team Hermes Hodios

Team Members:

Mayada Mannan Tufa

Nusrat Anwar Chowdhury

Syeda Sabiha Akhter

MD. Jahidul Ahsan

Institution: Leading University, Sylhet

## 2. Introduction & Problem Statement

International students often need to coordinate tuition, living expenses, funding sources, and cross-border payments while comparing fees, exchange rates, and delivery estimates. Details can be spread across different providers and institutions, and an unverified scholarship or exchange rate can lead to poor planning.

Nexora presents these tasks in one educational dashboard. It calculates budgets and funding gaps using deterministic arithmetic, displays a reference foreign-exchange (FX) rate when available, estimates transfer outcomes from entered fees and rates, and offers optional conversational guidance. Scholarship and university discovery provides targeted search links rather than claiming that awards or admissions are verified.

**Scope boundary:** Nexora is a prototype. It does not connect to bank accounts, provide guaranteed remittance quotes, verify scholarship eligibility, or send money.

## 3. System Architecture & Workflow

### 3.1 Architecture

1. **Frontend:** `templates/index.html` with CSS and JavaScript under `static/`. The browser collects user inputs and calls API endpoints.
2. **API layer:** FastAPI application in `app.py`, with request parsing, input validation, calculation routes, chat, and transfer-simulation workflows.
3. **Calculation services:** Deterministic budget, funding-gap, and transfer-estimate calculations. These calculations are separate from the generative chat response.
4. **External services:** Reference FX rate lookup through Frankfurter and an optional configured AI provider. Provider or network failures may prevent these features from working.
5. **Persistence:** SQLite database at the path configured by `NEXORA_DB_PATH` (defaults to `nexora.db`) stores demo operations and transfer intents.
6. **Testing:** `tests/test_app.py` uses FastAPI's test client and Pytest.

### 3.2 Typical Workflow

- The user enters budget inputs. The API validates the values and returns totals, a remaining balance, or a shortfall.
- The user requests an FX reference rate or enters a rate and fee to preview a transfer. The estimate is arithmetic based on those inputs and is not a provider quote.
- The user may prepare a transfer intent, review its values, and explicitly confirm a simulation. The resulting status is `SIMULATED_NOT_SENT`; no payment provider is called.
- The user can ask the chat assistant for general guidance. When a provider key is configured, the application may use an external AI provider; otherwise, it is intended to use a rule-based demo response.
- The user can access scholarship and university discovery links. These links help with research but do not verify eligibility, admission, awards, or deadlines.

### 3.3 Main Components

| Component | Responsibility |
|---|---|
| `app.py` | FastAPI routes, input validation, calculations, chat integration, and simulated operations |
| `templates/index.html` | Dashboard and interface structure |
| `static/style.css` | Visual styling and responsive layout |
| `static/script.js` | Frontend interactions and API calls |
| `static/chat.js` | Chat interface behavior |
| `tests/test_app.py` | Automated API and behavior tests |
| `nexora.db` | Local prototype storage; generated or used at runtime |
| `requirements.txt` | Python dependency list |
| `.env.example` | Example environment-variable configuration with placeholders |

File responsibilities should be checked against the final source files before submission.

## 4. Technology Stack

- **Programming language:** Python
- **Backend framework:** FastAPI
- **Application server:** Uvicorn
- **Frontend:** HTML, CSS, JavaScript, and Jinja2 templates
- **Database:** SQLite
- **HTTP requests:** Requests and/or HTTPX, as configured in the source
- **Optional AI integration:** Gemini or OpenAI provider configured on the server
- **FX reference source:** Frankfurter, when available
- **Testing:** Pytest and FastAPI TestClient
- **Development environment:** Python virtual environment on Linux/Chromebook or another compatible Python environment

Optional AI and external rate lookup depend on configuration and network availability.

## 5. Core Features

### 5.1 Student Budget Planning

The application accepts financial inputs and calculates budget totals and remaining balance or shortfall. These calculations use deterministic arithmetic and are intended to help students organize estimated income and expenses.

### 5.2 Tuition and Funding-Gap Planning

The funding planner compares total expected costs with available funds and confirmed funding. Only confirmed scholarships or other confirmed funding should be counted as confirmed resources. The resulting gap is an estimate based on user-provided values.

### 5.3 Currency Reference Rate and Transfer Estimation

The application can retrieve a reference FX rate from Frankfurter when available. It can also estimate the recipient amount from an amount, fee, and exchange rate supplied by the user.

Reference rates are not guaranteed remittance quotes. User-entered provider rates and fees are not independently verified. Delivery time is meaningful only when the user supplies a provider estimate.

### 5.4 Review-and-Confirm Transfer Simulation

The application creates a sandbox transfer intent and keeps it in an awaiting-confirmation state until explicit confirmation. It then records the status `SIMULATED_NOT_SENT`.

This demonstrates a review-and-confirm workflow, but no payment network or provider is integrated and no money moves.

### 5.5 AI Chat Assistant

The chat uses a configured AI provider when available; otherwise, a demo/rule-based fallback is intended. Chat provides general guidance and is not a trusted calculation engine or authority for financial decisions. Deterministic finance endpoints should be used for numeric results.

AI output can be inaccurate and should be checked against official sources.

### 5.6 Scholarship and University Discovery

The discovery feature creates search links based on user-provided profile fields. The results are discovery links, not a verified database of awards, admissions, eligibility, amounts, or deadlines.

### 5.7 Additional Interface Demonstrations

Any additional cards or interface modules should be described only to the extent supported by the code. They must not be presented as live bank, loan, OCR, tax, transcript, rewards, or payment integrations unless those integrations are implemented and tested.

## 6. Security & Privacy

- Supported currency values and bounded numeric inputs are applied to key finance endpoints.
- API credentials are expected in server-side environment variables, not browser code.
- Baseline headers include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, a referrer policy, and a permissions policy.
- Simulated operation creation requires explicit confirmation and is clearly labelled as non-payment.
- The prototype has no authentication or per-student authorization/isolation. Stored intents and operation logs must not be considered private between users if publicly deployed.
- SQLite is prototype persistence and may not be durable on ephemeral hosts.
- Optional model mode may send the user's question and limited context to a third-party AI provider. Provider terms and data-handling practices apply.
- Do not submit passwords, card details, passport numbers, account credentials, or sensitive financial data.

### 6.1 Known Limitations and Next Steps

Before real-user deployment, the project would need authentication and per-user authorization, rate limiting, structured logging and monitoring, database migrations and managed database controls, retention and backup policies, stronger provider timeouts and error handling, privacy disclosures, and independent security testing.

A production transfer integration would require an approved provider, secure authorization, reconciliation, compliance review, and extensive testing.

### 6.2 Verification and Evidence

Run the following from the project root:

```bash
python -m pytest tests/test_app.py -q
```

Preserve the actual output as testing evidence.

During development, a previous run reported **15 passed and 1 failed**. The failing test was `test_chat_demo_without_key`, which expected `demo` but received `ai`. This document does not claim that the test suite passes. Check provider/environment variables, investigate the failure, and rerun the tests before reporting the final status.


## Optional Ollama Cloud Integration

The application supports an optional Ollama Cloud chat provider. Configure `NEXORA_AI_PROVIDER=ollama`, provide `OLLAMA_API_KEY` as a server-side secret, and set `OLLAMA_MODEL` to an available model. The current code defaults to `gpt-oss:120b`. This integration calls the Ollama Cloud API and does not indicate that a local Ollama model is running.



## Chat agent orchestration (demo mode)

When no provider API key is configured, `/api/chat` uses an explainable local orchestration loop: intent routing → deterministic capability/tool selection → calculation/checklist result → recommendation. Budget context includes the dashboard's tuition, housing, food, transport, and other categories, which are summed into planned expenses. The response returns `agentic`, `plan`, and `tool_calls` for demo observability. This is a small custom Python implementation, not a third-party agent framework. It makes no live-rate claims and cannot send money. Existing Gemini/OpenAI/Ollama provider paths remain in place.

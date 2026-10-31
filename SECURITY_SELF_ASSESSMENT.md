
# Nexora AI — Security Self-Assessment
Competition:* FinTechathon 2026 — International Track, Topic C  
Team:Team Hermes Hodios  
Institution: Leading University, Sylhet
## 1. Executive Security Summary

**Scope:** Educational prototype for student budgeting, tuition funding-gap estimates, reference FX rates, transfer cost previews, optional AI chat, discovery links, and simulated transfer workflows.

Nexora implements basic input validation, server-side environment-based API key configuration, baseline browser security headers, and explicit confirmation for simulated operations. It is **not production-ready** and is not suitable for real money movement, banking credentials, or sensitive financial accounts.

This self-assessment is a project disclosure, not a certification or independent security audit.

## 2. Authentication & Access Control

### Current State

- No login, user identity, role system, or per-student authorization/isolation is implemented.
- The prototype has no privileged banking/payment tier.
- Transfer preparation and confirmation are sandbox workflow demonstrations only.
- Operation logs and stored intents must not be treated as private user-specific records on a public deployment.

### Risks

A public instance could allow visitors to view or affect shared prototype records, depending on exposed routes and deployment configuration. There is no account boundary that isolates one student's data from another.

### Required Before Production

Implement secure authentication, server-side authorization on every user-owned record, per-user database scoping, session protection, abuse controls, and security testing.

Do not expose the current prototype as a private financial service.

## 3. Data Protection & Privacy

### Data Handled

- User-entered budget and transfer-estimate values.
- Transfer-intent labels and numeric details for the sandbox workflow.
- Simulated operation status, amount, currency, and timestamps in SQLite.
- If an AI provider is enabled, the user's question and limited context may be sent to that provider.

### Current Safeguards

- API keys should be set in server environment variables and not placed in frontend source.
- `.env` and real secrets should not be committed. `.env.example` may contain placeholders only.
- Avoid collecting unnecessary personal information; use synthetic data for demos.
- Do not enter passwords, card data, passport numbers, account credentials, or sensitive financial records.

### Gaps

No formal retention/deletion workflow, user consent management, encryption-at-rest configuration, backup policy, or independent privacy review is documented.

SQLite files can contain demo records and should be inspected before sharing. The database file is intentionally excluded from the prepared submission archive to reduce accidental data disclosure; the app can create it on startup.

## 4. FinTech & API Security

### Controls in the Prototype

- Core endpoints validate numeric values and restrict supported currencies.
- Chat requests have a length limit and constrained context.
- Baseline headers include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, and `Permissions-Policy`.
- Simulated operations require an explicit `confirm: true` input.
- Transfer intent confirmation returns `SIMULATED_NOT_SENT`; no payment network is contacted.
- Finance calculations are deterministic endpoints, separate from model-generated chat text.

### Key Risks

- No rate limiting, formal abuse monitoring, or production-grade operational alerting.
- AI responses can hallucinate and may be influenced by prompt injection; model text must never authorize financial actions.
- FX reference data is not a guaranteed remittance quote and may be unavailable or delayed.
- Third-party model and FX services have their own availability, terms, and data-handling practices.
- No formal penetration test, independent audit, or complete production threat assessment has been completed.

### Required Mitigations Before Real-World Use

Use an approved payment provider and its secure authorization model. Add authentication and per-user access control, rate limiting, request/response logging with sensitive-data redaction, secrets rotation, provider timeouts and error handling, database migrations and managed persistence, dependency scanning, threat modeling, and independent security review.

Add idempotency and reconciliation appropriate to the actual provider before any live transaction integration.

## 5. Compliance & Threat Mitigation

| Threat | Current Mitigation | Remaining Gap |
|---|---|---|
| Invalid or extreme numeric inputs | Validation and bounded inputs on core calculation endpoints | Expand validation review to every route and add fuzz testing |
| Accidental real-payment claim | Explicit sandbox status `SIMULATED_NOT_SENT`; no payment provider integration | Maintain clear disclosures in the UI, demo, and documentation |
| API key exposure | Environment-variable configuration; keys are not intended for frontend use | Check deployment secrets and repository history; rotate exposed keys |
| AI misinformation/prompt injection | Separate deterministic calculation endpoints and non-payment workflow | Add stronger output checks, evaluation, monitoring, and user warnings |
| Shared data exposure | No sensitive data should be entered; prototype-only use | Authentication and per-user data isolation are absent |
| Provider outage or stale rate | Availability issues may affect reference lookup | Add timeouts, monitoring, cache freshness indicators, and fallback disclosure |
| Abuse or unexpected API costs | No model key is required for demo mode | Add rate limits, quotas, and abuse monitoring before public deployment |
| Data loss or accidental database sharing | Database excluded from prepared archive | Establish retention, backups, access controls, and secure deletion for production |

### Safe Demo Checklist

- [ ] Use synthetic budgets and fictional recipient labels.
- [ ] Confirm no real API keys or `.env` files are included in the submission.
- [ ] Confirm `nexora.db`, local virtual environments, cache files, and personal records are excluded.
- [ ] Show that a confirmed sandbox action is labelled `SIMULATED_NOT_SENT`.
- [ ] State clearly that no money is sent and no provider is connected.
- [ ] Capture actual test output; do not claim tests passed if any fail.
- [ ] Credit external APIs, libraries, templates, and AI-assisted contributions as required by competition rules.

### Readiness Conclusion

**Competition prototype only. Not approved for real financial activity.**

The current design demonstrates budgeting, cost estimation, discovery, and a simulated review/confirmation flow. Real-user or live-payment deployment requires a substantially stronger security, privacy, compliance, and operational design, plus independent testing.

## Ollama Cloud Security Considerations

Ollama Cloud is an optional external AI provider. Store `OLLAMA_API_KEY` only in private server environment settings; never commit real credentials or expose them in frontend code. Prompts and the context sent by the application may be processed by the selected provider. Review its privacy and retention terms before use. This integration has not been independently security-audited, and AI responses may be inaccurate.


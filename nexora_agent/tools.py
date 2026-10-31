"""Nexora tool belt: plain, testable Python functions shared by the LangChain agent and the offline agent.

Every tool returns a JSON-serialisable dict. Nothing here moves money; `prepare_transfer`
only creates a sandbox intent that a HUMAN must confirm in the UI (the LLM never gets a confirm tool).
"""
import math, time, uuid
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote_plus

import requests

CURRENCIES = {"BDT", "EUR", "USD", "GBP", "CNY"}
_db_factory = None


def set_db(factory):
    global _db_factory
    _db_factory = factory


def _money(x) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _num(v, name, allow_zero=True):
    try:
        n = float(v)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number")
    if not math.isfinite(n) or n < 0 or n > 1e12 or (n == 0 and not allow_zero):
        raise ValueError(f"{name} must be {'positive' if not allow_zero else 'non-negative'} and within limits")
    return n


def _cur(c, name="currency"):
    c = str(c or "").upper()
    if c not in CURRENCIES:
        raise ValueError(f"{name} must be one of {sorted(CURRENCIES)}")
    return c


def budget_check(available_funds: float, total_expenses: float, currency: str = "BDT") -> dict:
    """Compare available funds with total planned expenses for one period. Returns remaining balance and status."""
    f, e, c = _num(available_funds, "available_funds"), _num(total_expenses, "total_expenses"), _cur(currency)
    rem = f - e
    return {"currency": c, "available_funds": _money(f), "total_expenses": _money(e), "remaining": _money(rem),
            "status": "shortfall" if rem < 0 else "surplus" if rem > 0 else "break_even",
            "buffer_pct": round(rem / f * 100, 1) if f else None}


def funding_gap(available_funds: float, tuition: float, living: float, other: float = 0,
                confirmed_scholarship: float = 0, currency: str = "USD") -> dict:
    """Tuition + living funding-gap plan. Only CONFIRMED scholarships count; pending awards must not be passed in."""
    f, t, l, o, s = (_num(x, n) for x, n in [(available_funds, "available_funds"), (tuition, "tuition"),
                                            (living, "living"), (other, "other"), (confirmed_scholarship, "confirmed_scholarship")])
    c = _cur(currency)
    total = t + l + o
    rem = f + s - total
    return {"currency": c, "total_costs": _money(total), "confirmed_funding": _money(f + s),
            "remaining": _money(rem), "funding_gap": _money(max(0, -rem)),
            "coverage_pct": round((f + s) / total * 100, 1) if total else None,
            "status": "shortfall" if rem < 0 else "surplus" if rem > 0 else "break_even"}


def get_fx_rate(base: str, quote: str) -> dict:
    """Fetch the latest reference FX rate (not a provider quote). May fail offline; then ask the user for an offered rate."""
    try:
        b, q = _cur(base, "base"), _cur(quote, "quote")
    except ValueError as e:
        return {"error": str(e)}
    if b == q:
        return {"base": b, "quote": q, "rate": 1.0, "source": "same currency"}
    try:
        r = requests.get(f"https://api.frankfurter.dev/v2/rate/{b}/{q}", timeout=(3, 6))
        r.raise_for_status()
        p = r.json()
        rate = float(p["rate"])
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError("bad rate")
        return {"base": b, "quote": q, "rate": rate, "date": p.get("date"), "source": "Frankfurter reference rate"}
    except Exception:
        return {"error": "Live reference rate unavailable right now; ask the user for the provider's offered rate."}


def transfer_estimate(amount: float, rate: float, fee: float = 0, base: str = "USD", quote: str = "BDT") -> dict:
    """Estimate recipient amount = (amount - fee) * rate, using a rate the user gave or get_fx_rate returned."""
    a, r, f = _num(amount, "amount", False), _num(rate, "rate", False), _num(fee, "fee")
    if f > a:
        raise ValueError("fee cannot exceed amount")
    recv = (Decimal(str(a)) - Decimal(str(f))) * Decimal(str(r))
    return {"send": _money(a), "fee": _money(f), "rate": r, "base": _cur(base, "base"), "quote": _cur(quote, "quote"),
            "estimated_recipient_amount": _money(recv), "effective_fee_pct": round(f / a * 100, 2),
            "note": "Illustrative estimate; real provider quotes may differ."}


def compare_providers(amount: float, providers: list) -> dict:
    """Rank USD->BDT providers by recipient amount. providers = [{name, rate, fee}] using user-entered quotes only."""
    a = _num(amount, "amount", False)
    rows = []
    for p in (providers or [])[:10]:
        try:
            rate, fee = float(p["rate"]), float(p.get("fee", 0))
            rows.append({"provider": str(p.get("name", "Provider"))[:60], "rate": rate, "fee": fee,
                         "recipient_amount": _money(max(0, a - fee) * rate)})
        except (KeyError, TypeError, ValueError):
            continue
    rows.sort(key=lambda r: r["recipient_amount"], reverse=True)
    return {"send_usd": _money(a), "ranking": rows, "note": "Based only on quotes supplied by the user."}


def find_scholarships(destination: str = "", level: str = "", subject: str = "", nationality: str = "",
                      kind: str = "scholarship") -> dict:
    """Build targeted discovery links for scholarships or universities. Links are leads, not verified awards."""
    terms = " ".join(x.strip()[:80] for x in (destination, level, subject, nationality) if x)
    if kind == "university":
        q = "official university international admissions tuition requirements " + terms
    else:
        q = "scholarships international students official eligibility deadline " + terms
    return {"kind": kind, "links": [
        {"name": "Web search", "url": "https://www.google.com/search?q=" + quote_plus(q)},
        {"name": "University-funded awards (.edu)", "url": "https://www.google.com/search?q=" + quote_plus("site:.edu scholarship international students " + terms)},
        {"name": "Fulbright Foreign Student Program", "url": "https://foreign.fulbrightonline.org/"}],
        "warning": "Discovery leads only. Never count a scholarship as funding until it is confirmed."}


def prepare_transfer(recipient_label: str, amount: float, rate: float, fee: float = 0,
                     base: str = "USD", quote: str = "BDT") -> dict:
    """Prepare a SANDBOX transfer intent for human review. Sends nothing; the user must press Confirm in the UI."""
    label = str(recipient_label or "").strip()[:80]
    if not label:
        raise ValueError("recipient_label required (a name or nickname, never bank details)")
    est = transfer_estimate(amount, rate, fee, base, quote)
    iid = "NX-DEMO-" + uuid.uuid4().hex[:12].upper()
    if _db_factory is None:
        raise RuntimeError("database not configured")
    with _db_factory() as con:
        con.execute("""INSERT INTO transfer_intents (intent_id, recipient_label, send_amount, send_currency,
            receive_currency, fee, reference_rate, estimated_receive, status, provider_mode)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", (iid, label, est["send"], est["base"], est["quote"], est["fee"],
                                              est["rate"], est["estimated_recipient_amount"], "AWAITING_USER_CONFIRMATION", "SANDBOX_ONLY"))
    return {"intent_id": iid, "status": "AWAITING_USER_CONFIRMATION", "recipient": label, **est,
            "requires_human_confirmation": True, "message": "Prepared only. No money sent."}


def study_checklist(topic: str = "tuition") -> dict:
    """Return a verification checklist for a study-abroad finance topic (tuition, transfer, visa-funds)."""
    sets = {"transfer": ["Compare offered rate vs mid-market", "Add sending + receiving fees", "Check delivery time", "Get a dated quote"],
            "tuition": ["Confirm amount and due date on the official portal", "Separate tuition vs monthly living", "Count only confirmed funding", "Keep an emergency buffer"]}
    return {"topic": topic, "checks": sets.get(topic, sets["tuition"])}


# name -> (callable, label shown in the UI)
REGISTRY = {f.__name__: f for f in (budget_check, funding_gap, get_fx_rate, transfer_estimate, compare_providers,
                                    find_scholarships, prepare_transfer, study_checklist)}


def run_tool(name: str, args: dict) -> dict:
    """Execute one tool safely and return a trace entry. Errors become data the agent can react to."""
    t0 = time.perf_counter()
    fn = REGISTRY.get(name)
    if fn is None:
        return {"tool": name, "input": args, "error": "unknown tool", "ms": 0}
    try:
        result = fn(**(args or {}))
    except TypeError as e:
        result = {"error": f"bad arguments: {e}"}
    except Exception as e:  # validation errors, db errors
        result = {"error": str(e)[:200]}
    return {"tool": name, "input": args, "result": result, "ok": "error" not in result,
            "ms": int((time.perf_counter() - t0) * 1000)}

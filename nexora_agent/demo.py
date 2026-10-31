"""Offline agent: same tools, rule-based planner. Used when no model key works, so demos never break."""
import re

from .tools import run_tool

CUR = r"(usd|bdt|eur|gbp|cny)"
NUM = r"([\d][\d,]*(?:\.\d+)?)\s*(k\b)?"
SEEN = {}  # session_id -> last parsed facts, so follow-ups like "what if tuition is 12000?" still work


def _n(m):
    v = float(m.group(1).replace(",", ""))
    return v * 1000 if m.group(2) else v


def _grab(text, words):
    for w in words:
        m = re.search(rf"\b{w}\w*\D{{0,18}}?{NUM}", text) or re.search(rf"{NUM}\s*{CUR}?\s*(?:for|in|on)?\s*{w}", text)
        if m:
            return _n(m)
    return None


def _money(v, c):
    return f"{v:,.2f} {c}"


def _recipient(raw):
    m = re.search(r"\bto\s+((?:my\s+)?[A-Za-z][\w'-]*(?:\s+[A-Z][\w'-]*)?)", raw)
    if m and m.group(1).split()[0].lower() not in {"usd", "bdt", "eur", "gbp", "cny", "send", "the"}:
        return re.sub(r"^my\s+", "", m.group(1).strip(), flags=re.I).title()
    return "Demo recipient"


def run(message: str, context: dict, session_id: str = "") -> dict:
    t = message.casefold()
    cur_m = re.findall(CUR, t)
    ctx_cur = context.get("currency", "BDT")
    prev = SEEN.get(session_id, {})
    cur = cur_m[0].upper() if cur_m else prev.get("cur", ctx_cur)
    have = _grab(t, ["have", "income", "available", "funds", "savings", "budget"])
    tuition = _grab(t, ["tuition"])
    living = _grab(t, ["living", "rent", "housing"])
    amount = _grab(t, ["send", "transfer", "remit", "convert"])
    if amount is None:
        m = re.search(NUM + r"\s*" + CUR + r"\s*(?:to|into|in)\s*" + CUR, t)
        amount = _n(m) if m else None
    facts = {"have": have if have is not None else prev.get("have"), "tuition": tuition if tuition is not None else prev.get("tuition"),
             "living": living if living is not None else prev.get("living")}
    if session_id:
        SEEN[session_id] = {k: v for k, v in {**facts, "cur": cur}.items() if v is not None}
        if len(SEEN) > 200:
            SEEN.pop(next(iter(SEEN)))

    wants_fx = bool(re.search(r"\b(rate|exchange|convert|fx)\b|\bto\s+" + CUR, t))
    wants_send = bool(re.search(r"\b(send|transfer|remit|wire)\b", t))
    wants_schol = bool(re.search(r"scholarship|funding opportunit|find (a )?universit|admission", t))
    wants_tuition = tuition is not None or "tuition" in t  # remembered facts only fill gaps; they never trigger a plan
    wants_budget = bool(re.search(r"budget|afford|save|expense|surplus|shortfall|leftover|left over|balance|plan|cost", t)) or (context.get("income", 0) > 0 and context.get("expenses", 0) > 0 and not (wants_send or wants_schol))

    trace, plan, parts, pending = [], ["understand goal"], [], None
    tool = lambda n, a: trace.append(run_tool(n, a)) or trace[-1]

    if wants_tuition and facts["have"] is not None and (facts["tuition"] or 0) > 0:
        plan.append("compute funding gap")
        r = tool("funding_gap", {"available_funds": facts["have"], "tuition": facts["tuition"], "living": facts["living"] or 0, "currency": cur})
        if r["ok"]:
            x = r["result"]
            head = (f"Your funds cover {x['coverage_pct']}% of planned costs ({_money(x['total_costs'], cur)}). **Funding gap: {_money(x['funding_gap'], cur)}.**"
                    if x["status"] == "shortfall" else f"Good news: your funds cover planned costs of {_money(x['total_costs'], cur)} with {_money(x['remaining'], cur)} to spare.")
            parts.append(head)
            if x["status"] == "shortfall":
                parts.append("Closing it: (1) look for scholarships or university aid that is *confirmed* in writing, (2) ask the bursar about instalment plans, (3) trim flexible living costs. I only count confirmed funding.")
    elif wants_budget:
        inc = facts["have"] if facts["have"] is not None else context.get("income", 0)
        exp = context.get("expenses", 0)
        if facts["tuition"] is not None or facts["living"] is not None:
            exp = (facts["tuition"] or 0) + (facts["living"] or 0)
        plan.append("run budget check")
        if inc <= 0 and exp <= 0:
            parts.append("I can build your budget, but I need numbers. Fill in the planner or tell me e.g. “I have 1,000 BDT and costs are 1,250 BDT”.")
        else:
            r = tool("budget_check", {"available_funds": inc, "total_expenses": exp, "currency": cur})
            x = r["result"]
            if not r["ok"]:
                parts.append("I couldn't run that budget check: " + x.get("error", "invalid numbers") + ".")
            elif x.get("status") == "shortfall":
                parts.append(f"Your planned expenses are **{_money(abs(x['remaining']), cur)} more** than your funds ({_money(x['available_funds'], cur)} vs {_money(x['total_expenses'], cur)}).\nNext: confirm all figures cover the same period, protect tuition/housing/food first, then trim flexible costs.")
            elif x.get("status") == "break_even":
                parts.append(f"Funds and expenses match exactly ({_money(inc, cur)}), so there is no buffer. Build a small emergency reserve.")
            elif r["ok"]:
                parts.append(f"You have **{_money(x['remaining'], cur)} remaining** after expenses ({x['buffer_pct']}% buffer).\nNext: reserve upcoming tuition/one-time fees and recheck when costs or exchange rates change.")
    if wants_fx or wants_send:
        pair = re.search(CUR + r"\s*(?:to|into|->|→)\s*" + CUR, t)
        base, quote = (pair.group(1).upper(), pair.group(2).upper()) if pair else ("USD", "BDT")
        plan.append(f"fetch {base}/{quote} reference rate")
        fx = tool("get_fx_rate", {"base": base, "quote": quote})
        rate = fx["result"].get("rate") if fx["ok"] else None
        if rate:
            parts.append(f"Reference rate: 1 {base} ≈ {rate:,.4f} {quote} ({fx['result'].get('date')}). This is a mid-market reference, not a provider quote.")
        else:
            parts.append(f"I couldn't fetch a live {base}/{quote} rate just now. Tell me the provider's offered rate and I'll do the math.")
        fee_m = re.search(r"fee\D{0,12}" + NUM, t)
        fee = _n(fee_m) if fee_m else 0
        if amount and rate:
            plan.append("estimate recipient amount")
            e = tool("transfer_estimate", {"amount": amount, "rate": rate, "fee": fee, "base": base, "quote": quote})
            if e["ok"]:
                x = e["result"]
                parts.append(f"Sending {_money(x['send'], base)} (fee {_money(x['fee'], base)}) → recipient gets about **{_money(x['estimated_recipient_amount'], quote)}**.")
                if wants_send:
                    plan.append("prepare sandbox transfer for your confirmation")
                    p = tool("prepare_transfer", {"recipient_label": _recipient(message), "amount": amount, "rate": rate, "fee": fee, "base": base, "quote": quote})
                    if p["ok"]:
                        pending = p["result"]
                        parts.append(f"I prepared a **sandbox draft** for {pending['recipient']}. Nothing is sent until you press Confirm below.")
        elif wants_send:
            parts.append("Tell me the amount (and any fee) and I'll estimate what arrives and prepare a draft for you to confirm.")
    if wants_schol:
        plan.append("search scholarship leads")
        s = tool("find_scholarships", {"destination": "", "kind": "university" if "universit" in t else "scholarship"})
        parts.append("Here are targeted discovery leads (check each sponsor's official page; none count as funding until confirmed):\n" + "\n".join(f"• {l['name']}: {l['url']}" for l in s["result"]["links"]))
    if not parts:
        plan.append("route to capabilities")
        tool("study_checklist", {"topic": "tuition"})
        parts.append("Hi, I'm Nexora, your student-finance agent. I can run budget checks, size tuition funding gaps, pull FX rates, estimate transfers (and prepare a draft for you to confirm), and find scholarship leads.\n\nTry: “I have 8,000 USD, tuition is 10,000 and living costs 3,000. What should I do?” or “Send 200 USD to my sister, fee 3”.")
    plan.append("compose answer")
    return {"reply": "\n\n".join(parts), "trace": trace, "plan": plan}

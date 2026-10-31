"""Agent runtime: picks a provider, fails over (Gemini -> Ollama -> offline agent), returns one response shape."""
import logging, os, uuid

from . import demo, lc
from .tools import set_db

log = logging.getLogger("nexora.agent")


def configure(db_factory):
    set_db(db_factory)


def _providers():
    pref = os.getenv("NEXORA_AI_PROVIDER", "auto").lower()
    keys = {"gemini": bool(os.getenv("GEMINI_API_KEY", "").strip()), "ollama": bool(os.getenv("OLLAMA_API_KEY", "").strip())}
    order = [p for p in ([pref] if pref in keys else []) + ["gemini", "ollama"] if keys.get(p)]
    return list(dict.fromkeys(order))


def run_agent(message: str, context: dict, session_id: str = "") -> dict:
    sid = (session_id or "")[:64] or uuid.uuid4().hex
    errors = []
    for provider in _providers():
        try:
            out = lc.run(provider, message, context, sid)
            mode, name = "ai", provider.capitalize()
            break
        except Exception as exc:  # missing package, bad key, timeout, rate limit...
            log.warning("%s agent failed: %s", provider, type(exc).__name__)
            errors.append(provider)
    else:
        out = demo.run(message, context, sid)
        mode, name = "demo", "Nexora offline agent"
    pending = next((t["result"] for t in reversed(out["trace"]) if t["tool"] == "prepare_transfer" and t.get("ok")), None)
    return {"reply": out["reply"], "mode": mode, "agent": "Nexora", "agentic": True, "provider": name,
            "framework": out.get("engine", "LangChain") if mode == "ai" else "built-in planner", "session_id": sid,
            "plan": out["plan"], "tool_calls": out["trace"], "pending_confirmation": pending, "fallback_from": errors or None}

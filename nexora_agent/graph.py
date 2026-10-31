"""LangGraph workflow:  agent -> (tools -> agent)* -> self_review -> END.

The self-review node is a second LLM pass that audits the draft answer against the tool results
(no invented numbers, no claim that money moved) and rewrites it if needed.
"""
import json
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from .tools import run_tool

REVIEW_PROMPT = """You are a strict finance QA reviewer. Compare the DRAFT answer with the TOOL RESULTS.
If every number in the draft matches the tool results, nothing claims money was sent or accounts accessed, and no
unconfirmed scholarship is counted as funding, reply with exactly: OK
Otherwise reply with ONLY the corrected final answer for the student (same friendly style, no mention of this review)."""


class State(TypedDict):
    messages: Annotated[list, add_messages]
    steps: int
    trace: list
    final: str
    revised: bool


def _text(msg) -> str:
    c = msg.content
    return c.strip() if isinstance(c, str) else "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in c).strip()


def run_graph(llm_plain, llm_tools, messages: list, max_steps: int = 6):
    def agent(state: State):
        model = llm_tools if state["steps"] < max_steps else llm_plain  # out of budget: must answer now
        return {"messages": [model.invoke(state["messages"])]}

    def tools(state: State):
        out, trace = [], list(state["trace"])
        for call in state["messages"][-1].tool_calls:
            entry = run_tool(call["name"], call["args"])
            trace.append(entry)
            out.append(ToolMessage(content=json.dumps(entry.get("result"), default=str)[:4000],
                                   tool_call_id=call["id"], name=call["name"]))
        return {"messages": out, "trace": trace, "steps": state["steps"] + 1}

    def self_review(state: State):
        draft = _text(state["messages"][-1])
        evidence = json.dumps([{"tool": t["tool"], "result": t.get("result")} for t in state["trace"]], default=str)[:6000]
        verdict = _text(llm_plain.invoke([SystemMessage(REVIEW_PROMPT),
                                          HumanMessage(f"TOOL RESULTS:\n{evidence}\n\nDRAFT:\n{draft}")]))
        ok = verdict.upper().startswith("OK") or not verdict
        return {"final": draft if ok else verdict, "revised": not ok}

    def route(state: State):
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None) and state["steps"] < max_steps:
            return "tools"
        return "self_review" if state["trace"] else END  # only audit answers that used tools/numbers

    g = StateGraph(State)
    g.add_node("agent", agent)
    g.add_node("tools", tools)
    g.add_node("self_review", self_review)
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", route, {"tools": "tools", "self_review": "self_review", END: END})
    g.add_edge("tools", "agent")
    g.add_edge("self_review", END)
    state = g.compile().invoke({"messages": messages, "steps": 0, "trace": [], "final": "", "revised": False},
                               {"recursion_limit": 25})
    return state["final"] or _text(state["messages"][-1]), state["trace"], state["revised"]

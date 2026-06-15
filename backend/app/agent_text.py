"""Text-mode Ada — the exact same persona, tools, grounding, and playbook as the voice agent,
driven over chat-completions so the recursive loop can run hundreds of fast, cheap calls.

`agent_reply` runs a tool-calling loop: the model may call lookup_knowledge / save_lead_field /
set_outcome / escalate (executed server-side via the shared CallSession) before producing the
spoken line. Production voice reuses the same CallSession.execute_tool, so behavior matches."""
from __future__ import annotations

import json

from . import persona
from .openai_client import chat
from .session import CallSession

_MAX_TOOL_HOPS = 4


async def agent_reply(session: CallSession, history: list[dict]) -> tuple[str, list[dict]]:
    """history is a list of {role, content} (role in user/assistant) representing the dialogue
    from Ada's perspective (prospect = user). Returns (reply_text, updated_history)."""
    messages = [{"role": "system", "content": session.system_prompt()}] + history
    for _ in range(_MAX_TOOL_HOPS):
        msg = await chat(messages, model=None, tools=persona.tools_for_chat(),
                         temperature=0.6)
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            text = (msg.get("content") or "").strip()
            session.record_turn("agent", text)
            session.log_ask()
            history.append({"role": "assistant", "content": text})
            return text, history
        # execute tools, append results, loop again
        messages.append({"role": "assistant", "content": msg.get("content"),
                         "tool_calls": tool_calls})
        for tc in tool_calls:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            result = await session.execute_tool(fn, args)
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
    # Tool loop exhausted — force a plain reply.
    msg = await chat(messages + [{"role": "system",
                                  "content": "Now give your spoken reply to the prospect."}],
                     temperature=0.5)
    text = (msg.get("content") or "Could you tell me a bit more?").strip()
    session.record_turn("agent", text)
    history.append({"role": "assistant", "content": text})
    return text, history


async def agent_opening(session: CallSession) -> tuple[str, list[dict]]:
    """Ada's first line."""
    history: list[dict] = [{"role": "user", "content": "(call connected)"}]
    return await agent_reply(session, history)

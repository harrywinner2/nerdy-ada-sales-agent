"""CallSession — shared state + tool execution for a single conversation, used identically by
the Realtime voice socket and the text-mode self-play agent. This is what guarantees the agent
behaves the same on a phone call and in an experiment, so KPIs transfer.

A tool call is where most decisions get logged: a KB lookup is an `answer` decision, a saved
field advances discovery, an outcome resolves the call, an escalation is its own decision."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import kb, memory, persona, playbook
from .pii import Redactor


@dataclass
class CallSession:
    call_id: str
    lead_id: str
    channel: str            # web | phone | sim
    variant: dict
    version_tag: str
    profile: dict = field(default_factory=dict)
    redactor: Redactor = field(default_factory=Redactor)
    turn_index: int = -1
    last_grounded: bool = False

    @classmethod
    def begin(cls, channel: str, lead_id: str | None = None, contact: str | None = None,
              variant: dict | None = None) -> "CallSession":
        lead = memory.get_or_create_lead(lead_id=lead_id, contact=contact)
        variant = variant or persona.active_variant()
        vtag = persona.version_tag(variant)
        cid = memory.start_call(channel, vtag, lead_id=lead["id"])
        return cls(call_id=cid, lead_id=lead["id"], channel=channel, variant=variant,
                   version_tag=vtag, profile=memory.get_profile(lead["id"]))

    def system_prompt(self) -> str:
        return persona.build_system_prompt(
            profile=self.profile,
            memory_summary=memory.memory_summary(self.lead_id),
            variant=self.variant,
        )

    def record_turn(self, role: str, text: str) -> int:
        clean = self.redactor.redact(text or "")
        self.turn_index = memory.add_turn(self.call_id, role, clean)
        return self.turn_index

    def log_ask(self, rationale: str = "") -> None:
        """Log the implicit next-question decision based on current playbook state."""
        cands = playbook.next_candidates(self.profile)
        if playbook.ready_to_close(self.profile):
            memory.log_decision(self.call_id, max(self.turn_index, 0), "pivot_close",
                                cands, 0.8, rationale or "all required fields gathered")
        elif cands:
            memory.log_decision(self.call_id, max(self.turn_index, 0), "ask", cands, 0.7,
                                rationale or f"prioritized discovery: {cands[0]['field']}")

    async def execute_tool(self, name: str, args: dict) -> str:
        """Run a server-side tool and return a string result for the model."""
        if name == "lookup_knowledge":
            res = await kb.lookup(args.get("query", ""))
            self.last_grounded = res["grounded"]
            cites = ", ".join(c["title"] for c in res["citations"]) or "none"
            memory.log_decision(
                self.call_id, max(self.turn_index, 0), "answer", res["citations"],
                res["scores"][0] if res["scores"] else None,
                f"grounded:{res['grounded']} cites:{cites}")
            if not res["grounded"]:
                return ("NO_GROUNDED_ANSWER. Tell the prospect you want to get this exactly "
                        "right and will confirm, then escalate. Do not invent facts.")
            return f"GROUNDED CONTEXT (answer only from this):\n{res['answer_context']}"

        if name == "save_lead_field":
            f, v = args.get("field", ""), args.get("value", "")
            if f:
                self.profile = memory.save_field(self.lead_id, f, v)
                self.log_ask(f"learned {f}")
            return f"saved {f}={v}"

        if name == "set_outcome":
            outcome = args.get("outcome", "not_now")
            memory.set_outcome(self.call_id, outcome, args.get("notes", ""))
            action = "disqualify" if outcome == "disqualified" else "pivot_close"
            memory.log_decision(self.call_id, max(self.turn_index, 0), action, [], 0.9,
                                f"outcome={outcome}")
            return f"outcome recorded: {outcome}"

        if name == "escalate":
            reason, sev = args.get("reason", ""), args.get("severity", "medium")
            memory.log_escalation(self.call_id, reason, sev)
            memory.log_decision(self.call_id, max(self.turn_index, 0), "escalate", [], 0.5,
                                f"{sev}: {reason}")
            return f"escalation flagged ({sev}). Acknowledge and continue gracefully."

        return f"unknown tool {name}"

    def finish(self) -> dict:
        from . import kpis
        bundle = memory.get_call_bundle(self.call_id)
        k = kpis.call_kpis(bundle)
        memory.end_call(self.call_id, k)
        return k

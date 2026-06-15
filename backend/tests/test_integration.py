"""Integration tests that hit the REAL OpenAI API (per the project's no-mock requirement).

Skipped automatically when OPENAI_API_KEY is absent so the deterministic suite still runs in
CI without a key. Kept small to stay cheap."""
import asyncio

import pytest

from app import config, kb, seed

pytestmark = pytest.mark.skipif(not config.have_openai(), reason="no OPENAI_API_KEY")


def test_kb_grounding_real():
    async def go():
        await seed.seed_kb(force=True)
        priced = await kb.lookup("how much per month for tutoring?")
        assert priced["grounded"] is True
        assert any("Pricing" in c["title"] or "expensive" in c["title"].lower()
                   for c in priced["citations"])
        offtopic = await kb.lookup("what is the capital of France")
        assert offtopic["grounded"] is False
    asyncio.run(go())


def test_single_self_play_call_real():
    """One short self-play call produces a transcript, decisions, and KPIs."""
    from app import db, experiments, persona, simulator

    async def go():
        db.init_db()
        experiments.ensure_baseline()
        await seed.seed_kb()
        res = await experiments.run_sim_call(
            persona.active_variant(), simulator.get("ready_buyer"), seed=0)
        assert len(res["transcript"]) >= 4
        assert res["kpis"]["decisions"] > 0
        assert res["judged"].get("realism", 0) >= 0.3
    asyncio.run(go())

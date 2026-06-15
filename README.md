# Ada — Nerdy's Autonomous AI Sales Agent

Ada is a voice AI that can hold a complete tutoring sales call from "hello" to a booked
consultation — over the web (browser mic) and over a real phone line (Twilio). She gathers the
information a human advisor would, remembers prior calls, answers policy/pricing/competitive
questions only from a grounded knowledge base, and decides turn by turn what to ask, when to
pivot toward a close, and when to escalate. Every call is fully observable, and the system
improves itself by running controlled experiments against honest, adversarial synthetic
prospects.

This is a working product, not a slide deck. The voice runs on the OpenAI Realtime API; the
relay, knowledge base, decisioning, memory, and the recursive-improvement loop are a Python
FastAPI service; the dashboard is React. It deploys as a single service.

- **Live app:** https://ada-web-production.up.railway.app
- **Source:** https://github.com/harrywinner2/nerdy-ada-sales-agent
- **Spec:** `docs/PRD-expanded.md` · **Built for:** Nerdy / Varsity Tutors (brief in `tmp3.pdf`)

---

## What's in the box

| Capability (from the PRD) | Where it lives |
|---|---|
| Real-time bidirectional voice, barge-in | `app/realtime.py` (OpenAI Realtime, speech-to-speech) |
| Web channel (test it yourself) | `/ws/web` + the Live Call page |
| Phone channel (end-to-end) | `app/main.py` Twilio routes + `/ws/twilio` |
| Cross-call memory | `app/memory.py` (SQLite leads + prior-call summary) |
| Prioritized discovery, skip-when-known | `app/playbook.py` |
| Grounded knowledge base (no hallucinated facts) | `app/kb.py` + `app/seed.py` |
| Real-time decisioning (ask / pivot / escalate) | `app/session.py` + decision log |
| Full observability dashboard | `frontend/` (Calls, Call detail, KPIs) |
| Recursive improvement loop | `app/experiments.py` + `app/simulator.py` |
| PII-protected transcripts | `app/pii.py` (substitution at write time) |

## Architecture in one picture

The browser or a phone connects to a FastAPI relay. The relay holds a server-side WebSocket to
OpenAI's Realtime API — one socket carrying audio both ways with built-in voice-activity
detection, so turn-taking and barge-in feel natural. The model can call server-side tools
(knowledge lookup, save a discovered field, set the outcome, escalate); those tool calls are
also where most decisions get logged. Everything lands in SQLite, which doubles as memory and
the observability store. The same agent logic runs in *text* mode against synthetic prospects
to power the improvement loop, so gains transfer back to live voice. Full rationale for each
choice is in `docs/PRD-expanded.md` §2.

## Run it locally

You need Python 3.11+, Node 20+, and an OpenAI API key. Twilio is optional (only the phone
channel needs it).

```bash
# 1. secrets — never committed
cp .env.example .env            # then fill in OPENAI_API_KEY (and Twilio if you want phone)

# 2. backend
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m app.seed               # embeds the knowledge base (real OpenAI embeddings)
uvicorn app.main:app --reload    # serves API + dashboard on :8000

# 3. dashboard (dev, hot-reload) — or skip and use the built version the backend serves
cd ../frontend
npm install && npm run dev        # proxies /api and /ws to :8000
```

Open http://localhost:8000, hit **Start call**, and talk to Ada.

To run a self-improvement experiment from the CLI:

```bash
cd backend && . .venv/bin/activate
python -c "import asyncio; from app import experiments; \
  print(asyncio.run(experiments.run_experiment(seeds=1, variant_count=2))['decision'])"
```

## The phone channel

Point your Twilio number's Voice webhook at `https://<your-app>/twilio/voice` (POST). Inbound
calls bridge straight to Ada. For an outbound "call my phone" demo, the dashboard's Live Call
page POSTs to `/twilio/dial`. Set `PUBLIC_BASE_URL` to your deployed https URL so the media
stream points at the right host.

## Tests

```bash
cd backend && . .venv/bin/activate && python -m pytest -q
```

The deterministic suite (PII, playbook, KPIs, memory, API) runs without a network. Two
integration tests hit the real OpenAI API and are skipped automatically if no key is set —
nothing is mocked, per the project's requirement.

## Deploy

A multi-stage `Dockerfile` builds the dashboard and serves it from FastAPI. On Railway: set
`OPENAI_API_KEY` (and Twilio vars) as service variables, deploy, then set `PUBLIC_BASE_URL` to
the assigned URL and point Twilio at it. See `docs/deploy.md`.

## Documentation

- `docs/PRD-expanded.md` — the engineering spec
- `docs/recursive-improvement.md` — how the loop works + the before/after result
- `docs/decision-log.md` — what "decision logging" means here, and key build decisions
- `docs/failure-modes.md` — how Ada fails and what we do about it
- `docs/research-notes.md` — what we tried and learned
- `docs/limitations.md` — honest boundaries

> **Security note:** API keys live only in the untracked `.env` and the deploy secret store.
> Rotate the keys used for this build after the engagement.

# BUILD LOG — Nerdy Autonomous AI Sales Agent

Append-only. One line per meaningful decision or phase transition.

- intake: PRD from pasted text + tmp3.pdf (3pp). Channels = **web + Twilio phone**. Data = **synthesize via self-play**. Browser = **Playwright** (installed local + MCP registered). Deploy = **Railway**.
- preflight: PASS git/gh(harrywinner2)/node/npm; railway+vercel+wrangler authed; ffmpeg present; Playwright Chromium installed.
- arch: OpenAI **Realtime API (speech-to-speech)** voice core; **FastAPI** relay; **React** dashboard; embedded **vector KB**; **self-play** recursive loop. Rationale: lowest-latency barge-in, all-OpenAI per provider access, Railway runs persistent WS natively.
- phase2: captured nerdy.com via Playwright. Tokens: Poppins/Karla, canvas #0F0928/#161C2C, accent cyan #17E2EA, magenta→violet→cyan gradient. -> design/style-guide.md
- phase3: ui/mockup.html single-file design artifact (all screens).
- phase4: backend done; 9 tests green (7 unit + 2 real-API). Frontend: React/Vite dashboard, 7 wired screens, built to backend/static.
- phase4: recursive loop RAN — baseline close 25% -> 75% (Value/ROI Framing), obj-res 0.67->1.0, decision=promoted_with_review. Honest: realism 0.94, 1 disqualified/arm.
- deploy: Railway service ada-web LIVE at https://ada-web-production.up.railway.app (health ok, openai+twilio true, 12 KB docs). Multi-stage Docker.
- verify: live site loads, 0 console errors; live experiment populates deployed dashboard.
- fix: migrated Realtime bridge to GA API shape (gpt-realtime rejected beta header: beta_api_shape_disabled). Nested audio config, no beta header, response.create greeting. Verified: live web socket returns greeting audio + transcript. PASS.

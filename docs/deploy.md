# Deploy (Railway)

One service, built from the root `Dockerfile` (stage 1 builds the React dashboard, stage 2 runs
FastAPI and serves the build). Railway runs persistent WebSockets, which the voice relay needs.

## First deploy

```bash
# from the repo root, logged in to railway
railway init            # or link an existing project
railway up              # builds the Dockerfile and deploys

# set runtime secrets (never committed)
railway variables --set OPENAI_API_KEY=sk-...
railway variables --set TWILIO_ACCOUNT_SID=AC...
railway variables --set TWILIO_AUTH_TOKEN=...
railway variables --set TWILIO_PHONE_NUMBER=+1...

# after the URL is assigned, tell the app its public origin (for Twilio media streams)
railway variables --set PUBLIC_BASE_URL=https://<your-app>.up.railway.app
```

Railway sets `$PORT`; the container's `CMD` already binds to it. The knowledge base is seeded on
container start (`python -m app.seed`), so the first boot embeds the docs.

## Wire the phone channel

In the Twilio console, set the number's **Voice → A call comes in** webhook to:

```
https://<your-app>.up.railway.app/twilio/voice   (HTTP POST)
```

Inbound calls now reach Ada. The dashboard's "Call my phone" button uses `/twilio/dial` for
outbound demo calls.

## Verify

```bash
curl https://<your-app>.up.railway.app/api/health
# expect: {"ok":true,"openai":true,"twilio":true,"kb_docs":12,...}
```

Then open the URL, hit **Start call**, and talk.

## Notes
- Persistence: SQLite lives in the container at `data/ada.db`. For durable history across
  redeploys, attach a Railway volume mounted at `/app/data` and set `DB_PATH=/app/data/ada.db`.
- Secret hygiene: `scripts/secret_guard.sh` is run before every push/deploy in this project; keys
  exist only in the untracked `.env` and Railway's variable store. Rotate them after the
  engagement.

"""FastAPI application — REST observability API, the web voice socket, the Twilio phone bridge,
and static serving of the React dashboard. One service, deployable to Railway."""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import config, db, experiments, kb, kpis, memory, persona, simulator
from .realtime import OpenAIRealtime
from .session import CallSession


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    experiments.ensure_baseline()
    yield


app = FastAPI(title="Ada — Nerdy AI Sales Agent", lifespan=lifespan)


# ============================ REST API ============================

@app.get("/api/health")
async def health() -> dict:
    return {
        "ok": True,
        "openai": config.have_openai(),
        "twilio": config.have_twilio(),
        "kb_docs": kb.doc_count(),
        "model": config.OPENAI_REALTIME_MODEL,
        "version": persona.version_tag(),
    }


@app.get("/api/overview")
async def overview() -> dict:
    return {"aggregate": kpis.aggregate(), "versions": kpis.versions()}


@app.get("/api/calls")
async def list_calls() -> dict:
    rows = db.query(
        "SELECT id, lead_id, channel, version_tag, outcome, started_at, ended_at, kpis_json "
        "FROM calls ORDER BY started_at DESC LIMIT 200")
    for r in rows:
        r["kpis"] = db.unj(r.pop("kpis_json"), {})
    return {"calls": rows}


@app.get("/api/calls/{call_id}")
async def call_detail(call_id: str) -> JSONResponse:
    bundle = memory.get_call_bundle(call_id)
    if not bundle:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(bundle)


@app.get("/api/knowledge")
async def knowledge() -> dict:
    return {"docs": kb.list_docs()}


@app.get("/api/personas")
async def personas() -> dict:
    return {"prospects": [{"key": p.key, "label": p.label, "fit": p.fit, "brief": p.brief}
                          for p in simulator.PROSPECTS]}


@app.get("/api/experiments")
async def list_experiments() -> dict:
    return {"experiments": experiments.list_experiments(),
            "variants": experiments.list_variants()}


@app.post("/api/experiments/run")
async def run_experiment(req: Request) -> JSONResponse:
    if not config.have_openai():
        return JSONResponse({"error": "OPENAI_API_KEY not set"}, status_code=400)
    body = {}
    try:
        body = await req.json()
    except Exception:
        pass
    seeds = int(body.get("seeds", 1))
    variant_count = int(body.get("variant_count", 2))
    prospects = body.get("prospects")
    summary = await experiments.run_experiment(
        seeds=seeds, variant_count=variant_count, prospects=prospects)
    return JSONResponse(summary)


# ============================ Web voice socket ============================

@app.websocket("/ws/web")
async def ws_web(client: WebSocket) -> None:
    await client.accept()
    session = CallSession.begin("web")

    async def on_audio_out(b64: str) -> None:
        await client.send_text(json.dumps({"type": "audio", "audio": b64}))

    async def on_barge_in() -> None:
        await client.send_text(json.dumps({"type": "barge_in"}))

    async def on_transcript(role: str, text: str) -> None:
        await client.send_text(json.dumps({"type": "transcript", "role": role, "text": text}))

    bridge = OpenAIRealtime(session, audio_format="pcm16", on_audio_out=on_audio_out,
                            on_barge_in=on_barge_in, on_transcript=on_transcript, greet=True)
    try:
        await bridge.connect()
    except Exception as e:  # noqa: BLE001
        await client.send_text(json.dumps({"type": "error", "message": f"realtime connect failed: {e}"}))
        await client.close()
        return

    await client.send_text(json.dumps({"type": "ready", "call_id": session.call_id,
                                       "version": session.version_tag}))
    pump = asyncio.create_task(bridge.pump())
    try:
        while True:
            raw = await client.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "audio":
                await bridge.send_audio(msg["audio"])
            elif msg.get("type") == "hangup":
                break
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        await bridge.close()
        pump.cancel()
        session.finish()


# ============================ Twilio phone bridge ============================

@app.post("/twilio/voice")
async def twilio_voice(request: Request) -> PlainTextResponse:
    """TwiML that opens a bidirectional Media Stream to /ws/twilio."""
    host = config.PUBLIC_BASE_URL.replace("https://", "").replace("http://", "").rstrip("/") \
        or request.url.hostname
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Connect><Stream url="wss://{host}/ws/twilio" /></Connect>'
        "</Response>"
    )
    return PlainTextResponse(twiml, media_type="text/xml")


@app.post("/twilio/dial")
async def twilio_dial(request: Request) -> JSONResponse:
    """Outbound call trigger (for the demo wow-moment): POST {to: '+1...'}"""
    if not config.have_twilio():
        return JSONResponse({"error": "twilio not configured"}, status_code=400)
    body = await request.json()
    to = body.get("to")
    if not to:
        return JSONResponse({"error": "missing 'to'"}, status_code=400)
    from twilio.rest import Client
    base = config.PUBLIC_BASE_URL or f"https://{request.url.hostname}"
    client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    call = client.calls.create(to=to, from_=config.TWILIO_PHONE_NUMBER,
                               url=f"{base}/twilio/voice")
    return JSONResponse({"sid": call.sid, "status": call.status})


@app.websocket("/ws/twilio")
async def ws_twilio(twilio_ws: WebSocket) -> None:
    await twilio_ws.accept()
    session = CallSession.begin("phone")
    stream_sid = {"v": None}

    async def on_audio_out(b64: str) -> None:
        if stream_sid["v"]:
            await twilio_ws.send_text(json.dumps({
                "event": "media", "streamSid": stream_sid["v"], "media": {"payload": b64}}))

    async def on_barge_in() -> None:
        if stream_sid["v"]:
            await twilio_ws.send_text(json.dumps({"event": "clear", "streamSid": stream_sid["v"]}))

    bridge = OpenAIRealtime(session, audio_format="g711_ulaw", on_audio_out=on_audio_out,
                            on_barge_in=on_barge_in, greet=True)
    try:
        await bridge.connect()
    except Exception as e:  # noqa: BLE001
        print("[twilio] realtime connect failed:", e)
        await twilio_ws.close()
        return
    pump = asyncio.create_task(bridge.pump())
    try:
        while True:
            raw = await twilio_ws.receive_text()
            data = json.loads(raw)
            ev = data.get("event")
            if ev == "start":
                stream_sid["v"] = data["start"]["streamSid"]
            elif ev == "media":
                await bridge.send_audio(data["media"]["payload"])
            elif ev == "stop":
                break
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        await bridge.close()
        pump.cancel()
        session.finish()


# ============================ Static React dashboard ============================

_DIST = Path(__file__).resolve().parents[1] / "static"


def _mount_static() -> None:
    if _DIST.exists():
        app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")


_mount_static()


@app.get("/{full_path:path}")
async def spa(full_path: str) -> HTMLResponse:
    index = _DIST / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text())
    return HTMLResponse(
        "<h1>Ada backend is running</h1><p>Dashboard build not found. "
        "API is live at <code>/api/health</code>.</p>")

"""OpenAI Realtime (speech-to-speech) bridge — the live voice core for both channels.

A server-side WebSocket to OpenAI carries audio both ways with server-side VAD (natural
turn-taking + barge-in). Tool calls (KB lookup, save field, outcome, escalate) are executed via
the shared CallSession, so a phone call and a web call behave identically. Transcripts are
captured per turn (PII-redacted in CallSession) for the observability store.

`OpenAIRealtime` is channel-agnostic; main.py supplies thin adapters for the browser (PCM16)
and Twilio Media Streams (G.711 μ-law)."""
from __future__ import annotations

import asyncio
import json
from typing import Awaitable, Callable

import websockets

from . import persona
from .config import OPENAI_API_KEY, OPENAI_REALTIME_URL, OPENAI_VOICE
from .session import CallSession


class OpenAIRealtime:
    def __init__(self, session: CallSession, *, audio_format: str,
                 on_audio_out: Callable[[str], Awaitable[None]],
                 on_barge_in: Callable[[], Awaitable[None]] | None = None,
                 on_transcript: Callable[[str, str], Awaitable[None]] | None = None,
                 greet: bool = True):
        self.session = session
        self.audio_format = audio_format          # "pcm16" (web) | "g711_ulaw" (twilio)
        self.on_audio_out = on_audio_out
        self.on_barge_in = on_barge_in
        self.on_transcript = on_transcript
        self.greet = greet
        self.ws: websockets.WebSocketClientProtocol | None = None
        self._agent_buf = ""
        self._closed = False

    async def connect(self) -> None:
        self.ws = await websockets.connect(
            OPENAI_REALTIME_URL,
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1",
            },
            max_size=None,
            ping_interval=20,
        )
        await self._configure()
        if self.greet:
            await self._create_response(
                "Greet the caller warmly as Ada from Nerdy, briefly say you can help find the "
                "right tutoring plan, and ask an opening question.")

    async def _configure(self) -> None:
        cfg = {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": self.session.system_prompt(),
                "voice": OPENAI_VOICE,
                "input_audio_format": self.audio_format,
                "output_audio_format": self.audio_format,
                "input_audio_transcription": {"model": "gpt-4o-mini-transcribe"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500,
                    "create_response": True,
                },
                "tools": persona.tools_for_realtime(),
                "tool_choice": "auto",
                "temperature": 0.7,
            },
        }
        await self._send(cfg)

    async def _send(self, obj: dict) -> None:
        if self.ws and not self._closed:
            await self.ws.send(json.dumps(obj))

    async def send_audio(self, b64: str) -> None:
        await self._send({"type": "input_audio_buffer.append", "audio": b64})

    async def _create_response(self, instructions: str | None = None) -> None:
        payload: dict = {"type": "response.create"}
        if instructions:
            payload["response"] = {"instructions": instructions}
        await self._send(payload)

    async def _refresh_instructions(self) -> None:
        """Push updated playbook state (after a field was saved) into the live session."""
        await self._send({"type": "session.update",
                          "session": {"instructions": self.session.system_prompt()}})

    async def pump(self) -> None:
        """Read OpenAI events until the socket closes."""
        assert self.ws is not None
        try:
            async for raw in self.ws:
                await self._handle(json.loads(raw))
        except (websockets.ConnectionClosed, asyncio.CancelledError):
            pass
        finally:
            self._closed = True

    async def _handle(self, evt: dict) -> None:
        t = evt.get("type", "")

        # ---- audio out (handle both GA + beta event names) ----
        if t in ("response.audio.delta", "response.output_audio.delta"):
            delta = evt.get("delta")
            if delta:
                await self.on_audio_out(delta)
            return

        # ---- barge-in: caller started talking ----
        if t == "input_audio_buffer.speech_started":
            if self.on_barge_in:
                await self.on_barge_in()
            await self._send({"type": "response.cancel"})
            return

        # ---- agent transcript ----
        if t in ("response.audio_transcript.delta", "response.output_audio_transcript.delta"):
            self._agent_buf += evt.get("delta", "")
            return
        if t in ("response.audio_transcript.done", "response.output_audio_transcript.done"):
            text = (evt.get("transcript") or self._agent_buf).strip()
            if text:
                self.session.record_turn("agent", text)
                self.session.log_ask()
                if self.on_transcript:
                    await self.on_transcript("agent", text)
            self._agent_buf = ""
            return

        # ---- caller (user) transcript ----
        if t == "conversation.item.input_audio_transcription.completed":
            text = (evt.get("transcript") or "").strip()
            if text:
                self.session.record_turn("prospect", text)
                if self.on_transcript:
                    await self.on_transcript("prospect", text)
            return

        # ---- tool call ----
        if t == "response.function_call_arguments.done":
            await self._run_tool(evt)
            return

        if t == "error":
            # surface but don't crash the bridge
            print("[realtime error]", json.dumps(evt.get("error", evt))[:300])
            return

    async def _run_tool(self, evt: dict) -> None:
        name = evt.get("name", "")
        call_id = evt.get("call_id")
        try:
            args = json.loads(evt.get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}
        result = await self.session.execute_tool(name, args)
        await self._send({
            "type": "conversation.item.create",
            "item": {"type": "function_call_output", "call_id": call_id, "output": result},
        })
        if name == "save_lead_field":
            await self._refresh_instructions()
        await self._create_response()

    async def close(self) -> None:
        self._closed = True
        if self.ws:
            await self.ws.close()

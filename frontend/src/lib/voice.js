// Voice client for the Ada live-call WebSocket.
// Handles mic capture (downsample -> PCM16 -> base64), gapless playback,
// and barge-in. PCM16 mono @ 24000 Hz both directions.
//
// Usage:
//   const v = new VoiceClient({ onTranscript, onState, onReady, onError })
//   await v.start()   // requests mic, opens WS, starts streaming
//   v.stop()          // hangs up + tears down

const SAMPLE_RATE = 24000
const MIC_BUFFER = 4096

function floatTo16BitPCM(input) {
  const out = new Int16Array(input.length)
  for (let i = 0; i < input.length; i++) {
    let s = Math.max(-1, Math.min(1, input[i]))
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff
  }
  return out
}

function downsampleBuffer(buffer, inputRate, outputRate) {
  if (outputRate >= inputRate) return buffer
  const ratio = inputRate / outputRate
  const newLength = Math.round(buffer.length / ratio)
  const result = new Float32Array(newLength)
  let offsetResult = 0
  let offsetBuffer = 0
  while (offsetResult < result.length) {
    const nextOffset = Math.round((offsetResult + 1) * ratio)
    let accum = 0
    let count = 0
    for (let i = offsetBuffer; i < nextOffset && i < buffer.length; i++) {
      accum += buffer[i]
      count++
    }
    result[offsetResult] = count ? accum / count : 0
    offsetResult++
    offsetBuffer = nextOffset
  }
  return result
}

function int16ToBase64(int16) {
  const bytes = new Uint8Array(int16.buffer, int16.byteOffset, int16.byteLength)
  let binary = ''
  const chunk = 0x8000
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk))
  }
  return btoa(binary)
}

function base64ToInt16(b64) {
  const binary = atob(b64)
  const len = binary.length
  const bytes = new Uint8Array(len)
  for (let i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i)
  // Ensure even byte length for Int16.
  const usable = len - (len % 2)
  return new Int16Array(bytes.buffer, 0, usable / 2)
}

export class VoiceClient {
  constructor({ onTranscript, onState, onReady, onError } = {}) {
    this.onTranscript = onTranscript || (() => {})
    this.onState = onState || (() => {})
    this.onReady = onReady || (() => {})
    this.onError = onError || (() => {})

    this.ws = null
    this.micCtx = null
    this.playCtx = null
    this.mediaStream = null
    this.source = null
    this.processor = null

    this.scheduled = [] // active playback source nodes
    this.nextStartTime = 0
    this.active = false

    // levels for the orb (0..1)
    this.micLevel = 0
    this.agentLevel = 0
    this.lastAgentAudioAt = 0
  }

  setState(partial) {
    this.onState({
      active: this.active,
      micLevel: this.micLevel,
      agentLevel: this.agentLevel,
      speaking: Date.now() - this.lastAgentAudioAt < 350,
      ...partial,
    })
  }

  async start() {
    if (this.active) return
    // Mic permission first so failures surface before opening the socket.
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch (e) {
      this.onError(
        e && e.name === 'NotAllowedError'
          ? 'Microphone permission denied. Allow mic access and try again.'
          : 'Could not access microphone. Check your device and browser permissions.'
      )
      return
    }

    try {
      const AC = window.AudioContext || window.webkitAudioContext
      this.micCtx = new AC()
      this.playCtx = new AC({ sampleRate: SAMPLE_RATE })
      // Some browsers create suspended contexts until a gesture; start() is gesture-driven.
      if (this.playCtx.state === 'suspended') await this.playCtx.resume()
      if (this.micCtx.state === 'suspended') await this.micCtx.resume()
    } catch (e) {
      this.onError('Audio engine failed to initialize in this browser.')
      this.cleanup()
      return
    }

    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${location.host}/ws/web`
    let ws
    try {
      ws = new WebSocket(url)
    } catch {
      this.onError('Could not open the live call connection.')
      this.cleanup()
      return
    }
    this.ws = ws

    ws.onopen = () => {
      this.active = true
      this.startMicPump()
      this.setState({ active: true })
    }
    ws.onmessage = (ev) => this.handleMessage(ev.data)
    ws.onerror = () => {
      this.onError('Live call connection error.')
    }
    ws.onclose = () => {
      if (this.active) {
        this.active = false
        this.setState({ active: false })
      }
      this.cleanup()
    }
  }

  startMicPump() {
    const ctx = this.micCtx
    this.source = ctx.createMediaStreamSource(this.mediaStream)
    this.processor = ctx.createScriptProcessor(MIC_BUFFER, 1, 1)
    this.source.connect(this.processor)
    // Connect to a muted gain so the processor runs without echoing the mic.
    const sink = ctx.createGain()
    sink.gain.value = 0
    this.processor.connect(sink)
    sink.connect(ctx.destination)

    this.processor.onaudioprocess = (e) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return
      const input = e.inputBuffer.getChannelData(0)

      // mic level for the orb
      let sum = 0
      for (let i = 0; i < input.length; i++) sum += input[i] * input[i]
      this.micLevel = Math.min(1, Math.sqrt(sum / input.length) * 4)

      const down = downsampleBuffer(input, ctx.sampleRate, SAMPLE_RATE)
      const pcm = floatTo16BitPCM(down)
      const b64 = int16ToBase64(pcm)
      try {
        this.ws.send(JSON.stringify({ type: 'audio', audio: b64 }))
      } catch {
        /* socket closing */
      }
      this.setState({})
    }
  }

  handleMessage(data) {
    let msg
    try {
      msg = JSON.parse(data)
    } catch {
      return
    }
    switch (msg.type) {
      case 'ready':
        this.onReady({ callId: msg.call_id, version: msg.version })
        break
      case 'audio':
        this.enqueueAudio(msg.audio)
        break
      case 'transcript':
        this.onTranscript({ role: msg.role, text: msg.text })
        break
      case 'barge_in':
        this.flushPlayback()
        break
      case 'error':
        this.onError(msg.message || 'The agent reported an error.')
        break
      default:
        break
    }
  }

  enqueueAudio(b64) {
    if (!this.playCtx) return
    const int16 = base64ToInt16(b64)
    if (!int16.length) return
    const float = new Float32Array(int16.length)
    for (let i = 0; i < int16.length; i++) float[i] = int16[i] / 0x8000

    // agent level for the orb
    let sum = 0
    for (let i = 0; i < float.length; i++) sum += float[i] * float[i]
    this.agentLevel = Math.min(1, Math.sqrt(sum / float.length) * 3)
    this.lastAgentAudioAt = Date.now()

    const buffer = this.playCtx.createBuffer(1, float.length, SAMPLE_RATE)
    buffer.copyToChannel(float, 0)
    const src = this.playCtx.createBufferSource()
    src.buffer = buffer
    src.connect(this.playCtx.destination)

    const now = this.playCtx.currentTime
    if (this.nextStartTime < now) this.nextStartTime = now + 0.02
    src.start(this.nextStartTime)
    this.nextStartTime += buffer.duration

    this.scheduled.push(src)
    src.onended = () => {
      this.scheduled = this.scheduled.filter((s) => s !== src)
    }
    this.setState({})
  }

  flushPlayback() {
    for (const src of this.scheduled) {
      try {
        src.onended = null
        src.stop()
        src.disconnect()
      } catch {
        /* already stopped */
      }
    }
    this.scheduled = []
    this.nextStartTime = this.playCtx ? this.playCtx.currentTime : 0
    this.agentLevel = 0
    this.setState({})
  }

  stop() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify({ type: 'hangup' }))
      } catch {
        /* ignore */
      }
    }
    this.active = false
    this.setState({ active: false })
    if (this.ws) {
      try {
        this.ws.close()
      } catch {
        /* ignore */
      }
    }
    this.cleanup()
  }

  cleanup() {
    this.flushPlayback()
    if (this.processor) {
      try {
        this.processor.onaudioprocess = null
        this.processor.disconnect()
      } catch {}
      this.processor = null
    }
    if (this.source) {
      try {
        this.source.disconnect()
      } catch {}
      this.source = null
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop())
      this.mediaStream = null
    }
    if (this.micCtx) {
      this.micCtx.close().catch(() => {})
      this.micCtx = null
    }
    if (this.playCtx) {
      this.playCtx.close().catch(() => {})
      this.playCtx = null
    }
    this.ws = null
    this.micLevel = 0
    this.agentLevel = 0
  }
}

export default VoiceClient

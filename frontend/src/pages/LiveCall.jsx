import { useEffect, useRef, useState } from 'react'
import VoiceClient from '../lib/voice'
import { api } from '../lib/api'
import { IconMic, IconStop, IconPhone } from '../components/icons'

const STEPS = [
  { t: 'Discover', d: 'Ada asks for the few facts that qualify a lead — goals, grade, timeline.' },
  { t: 'Ground', d: 'Every answer is pulled from the Knowledge Base. No invented pricing or claims.' },
  { t: 'Decide', d: 'Each turn she chooses: ask, answer, pivot to close, escalate, or disqualify.' },
  { t: 'Close or escalate', d: 'She books the consult when ready — or hands off when a human is needed.' },
]

function Orb({ state }) {
  const speaking = state.speaking
  const listening = state.active && !speaking && state.micLevel > 0.04
  const cls = !state.active ? 'idle' : speaking ? 'speaking' : listening ? 'listening' : 'idle'
  const level = speaking ? state.agentLevel : state.micLevel
  const bars = 7
  const scale = 1 + (state.active ? level * 0.18 : 0)

  return (
    <div className={`orb ${cls}`}>
      <div className="ring r1" />
      <div className="ring r2" />
      <div className="core" style={{ transform: `scale(${scale})` }} />
      {state.active && (
        <div className="orb-bars">
          {Array.from({ length: bars }).map((_, i) => {
            const center = Math.abs(i - (bars - 1) / 2)
            const falloff = 1 - center / bars
            const h = 8 + level * 46 * falloff + (Math.sin(Date.now() / 120 + i) + 1) * 4
            return <i key={i} style={{ height: `${h}px` }} />
          })}
        </div>
      )}
    </div>
  )
}

export default function LiveCall() {
  const clientRef = useRef(null)
  const scrollRef = useRef(null)
  const [transcript, setTranscript] = useState([])
  const [state, setState] = useState({ active: false, micLevel: 0, agentLevel: 0, speaking: false })
  const [version, setVersion] = useState(null)
  const [error, setError] = useState(null)
  const [starting, setStarting] = useState(false)

  const [twilioOk, setTwilioOk] = useState(false)
  const [phone, setPhone] = useState('')
  const [dialing, setDialing] = useState(false)
  const [dialMsg, setDialMsg] = useState(null)

  useEffect(() => {
    api.health().then((h) => setTwilioOk(!!h.twilio)).catch(() => {})
    return () => clientRef.current?.stop()
  }, [])

  // force re-render for orb animation while active
  const [, tick] = useState(0)
  useEffect(() => {
    if (!state.active) return
    const id = setInterval(() => tick((n) => n + 1), 60)
    return () => clearInterval(id)
  }, [state.active])

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [transcript])

  function start() {
    setError(null)
    setTranscript([])
    setVersion(null)
    setStarting(true)
    const client = new VoiceClient({
      onTranscript: ({ role, text }) =>
        setTranscript((prev) => [...prev, { role, text, id: Date.now() + Math.random() }]),
      onState: (s) => {
        setState(s)
        if (s.active) setStarting(false)
      },
      onReady: ({ version }) => setVersion(version),
      onError: (msg) => {
        setError(msg)
        setStarting(false)
      },
    })
    clientRef.current = client
    client.start()
  }

  function stop() {
    clientRef.current?.stop()
    clientRef.current = null
    setStarting(false)
  }

  async function dial(e) {
    e.preventDefault()
    if (!phone.trim()) return
    setDialing(true)
    setDialMsg(null)
    try {
      const r = await api.dial(phone.trim())
      setDialMsg({ ok: true, text: `Calling ${phone} — status: ${r.status}` })
    } catch (err) {
      setDialMsg({ ok: false, text: err.message || 'Dial failed' })
    } finally {
      setDialing(false)
    }
  }

  const stateLabel = !state.active
    ? 'Idle'
    : state.speaking
    ? 'Ada speaking'
    : state.micLevel > 0.04
    ? 'Listening'
    : 'Connected'

  return (
    <div className="fade-in">
      {error && (
        <div className="error-banner" style={{ marginBottom: 18 }}>
          {error}
        </div>
      )}

      <div className="live-grid">
        <div className="card orb-stage">
          <Orb state={state} />
          <div className="orb-state">
            {state.active && <span className="live-dot" />}
            {stateLabel}
            {version && (
              <span className="pill cyan" style={{ marginLeft: 4 }}>
                {version}
              </span>
            )}
          </div>
          <div className="orb-cta">
            {!state.active ? (
              <button className="btn primary lg" onClick={start} disabled={starting}>
                <IconMic style={{ width: 18, height: 18 }} />
                {starting ? 'Connecting…' : 'Start call'}
              </button>
            ) : (
              <button className="btn danger lg" onClick={stop}>
                <IconStop style={{ width: 18, height: 18 }} />
                End call
              </button>
            )}
          </div>
          <div className="lead" style={{ textAlign: 'center', maxWidth: 360 }}>
            Press start, allow microphone access, and speak naturally. Ada responds with voice
            and adapts turn by turn.
          </div>
        </div>

        <div className="card transcript-pane">
          <div className="card-head">
            <h3>Live transcript</h3>
            <span className="hint">
              <span className="mono" style={{ color: 'var(--accent)' }}>Ada</span> ·{' '}
              <span className="mono" style={{ color: '#b69bff' }}>You</span>
            </span>
          </div>
          <div className="transcript-scroll" ref={scrollRef}>
            {transcript.length === 0 ? (
              <div className="faint" style={{ margin: 'auto', textAlign: 'center' }}>
                Transcript will appear here as you talk.
              </div>
            ) : (
              transcript.map((t) => (
                <div key={t.id} className={`t-line ${t.role === 'agent' ? 'agent' : 'prospect'}`}>
                  <div className="who">{t.role === 'agent' ? 'Ada' : 'You'}</div>
                  {t.text}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', marginTop: 22 }}>
        <div className="card">
          <div className="card-head">
            <h3>How Ada decides</h3>
            <span className="hint">autonomous loop</span>
          </div>
          {STEPS.map((s, i) => (
            <div className="explainer-step" key={s.t}>
              <div className="n">{i + 1}</div>
              <div>
                <b>{s.t}</b>
                <p>{s.d}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="card">
          <div className="card-head">
            <h3>Call my phone</h3>
            <span className={`pill ${twilioOk ? 'ok' : 'dim'}`}>
              {twilioOk ? 'Twilio ready' : 'Twilio off'}
            </span>
          </div>
          <p className="lead" style={{ marginTop: 0 }}>
            Have Ada call you on a real phone line via Twilio — the same agent, over the
            telephone network.
          </p>
          <form className="phone-panel" onSubmit={dial}>
            <div className="grow">
              <label className="field-label">Phone number</label>
              <input
                className="input"
                placeholder="+1 555 123 4567"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                disabled={!twilioOk}
              />
            </div>
            <button className="btn primary" type="submit" disabled={!twilioOk || dialing || !phone.trim()}>
              <IconPhone style={{ width: 17, height: 17 }} />
              {dialing ? 'Dialing…' : 'Call me'}
            </button>
          </form>
          {dialMsg && (
            <div
              style={{ marginTop: 14, fontSize: 13, color: dialMsg.ok ? 'var(--ok)' : 'var(--bad)' }}
            >
              {dialMsg.text}
            </div>
          )}
          {!twilioOk && (
            <div className="faint" style={{ marginTop: 12, fontSize: 12 }}>
              Configure Twilio credentials on the backend to enable outbound calls.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

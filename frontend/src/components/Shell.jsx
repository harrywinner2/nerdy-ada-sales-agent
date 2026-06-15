import { NavLink, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import {
  IconLive,
  IconCalls,
  IconKnowledge,
  IconExperiments,
  IconPersonas,
  IconOverview,
} from './icons'

const NAV = [
  { to: '/', label: 'Live Call', Icon: IconLive, end: true },
  { to: '/calls', label: 'Calls', Icon: IconCalls },
  { to: '/knowledge', label: 'Knowledge Base', Icon: IconKnowledge },
  { to: '/experiments', label: 'Recursive Improvement', Icon: IconExperiments },
  { to: '/personas', label: 'Synthetic Prospects', Icon: IconPersonas },
  { to: '/overview', label: 'KPIs', Icon: IconOverview },
]

const TITLES = {
  '/': { h: 'Live Call', p: 'Talk to Ada in real time — she discovers, qualifies, and closes.' },
  '/calls': { h: 'Calls', p: 'Every conversation Ada has handled, with outcomes and discovery depth.' },
  '/knowledge': { h: 'Knowledge Base', p: 'The grounding sources Ada cites — no hallucinated facts.' },
  '/experiments': {
    h: 'Recursive Improvement',
    p: 'Ada runs experiments against synthetic prospects and promotes what wins.',
  },
  '/personas': {
    h: 'Synthetic Prospects',
    p: 'Honest, non-obedient prospects engineered to try to break the agent.',
  },
  '/overview': { h: 'KPIs', p: 'Performance across versions — the proof the agent is getting better.' },
}

function HealthPill() {
  const [h, setH] = useState(null)
  useEffect(() => {
    let alive = true
    const load = () =>
      api
        .health()
        .then((d) => alive && setH(d))
        .catch(() => alive && setH({ error: true }))
    load()
    const id = setInterval(load, 20000)
    return () => {
      alive = false
      clearInterval(id)
    }
  }, [])

  if (!h) {
    return <div className="health"><div className="skeleton" style={{ width: 180, height: 16 }} /></div>
  }
  if (h.error) {
    return (
      <div className="health">
        <span className="dot"><i className="off" /> backend unreachable</span>
      </div>
    )
  }
  return (
    <div className="health fade-in">
      <span className="meta">
        <b>{h.model || 'model'}</b>
      </span>
      <span className="divider-v" />
      <span className="meta">
        <b>{h.kb_docs ?? 0}</b> KB docs
      </span>
      <span className="divider-v" />
      <span className="dots">
        <span className="dot">
          <i className={h.openai ? 'on' : 'off'} /> OpenAI
        </span>
        <span className="dot">
          <i className={h.twilio ? 'on' : 'off'} /> Twilio
        </span>
      </span>
    </div>
  )
}

function Wordmark() {
  return (
    <div className="wordmark">
      <span className="mark">
        <svg viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="7" stroke="#fff" strokeWidth="2.4" />
          <circle cx="12" cy="12" r="2.4" fill="#fff" />
        </svg>
      </span>
      <div>
        <div className="name">Ada</div>
        <div className="sub">Nerdy AI Sales Agent</div>
      </div>
    </div>
  )
}

export default function Shell({ children }) {
  const loc = useLocation()
  const matchKey =
    loc.pathname.startsWith('/calls') && loc.pathname !== '/calls'
      ? '/calls'
      : loc.pathname
  const t = TITLES[matchKey] || TITLES['/calls']

  return (
    <div className="app">
      <div className="bg-field">
        <div className="blob b1" />
        <div className="blob b2" />
        <div className="blob b3" />
      </div>

      <aside className="sidebar">
        <Wordmark />
        <div className="nav-section">Workspace</div>
        <nav className="nav">
          {NAV.map(({ to, label, Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <Icon className="ic" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          Ada is autonomous: she decides what to ask, when to handle an objection, and when
          to escalate — grounded only in the Knowledge Base.
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="page-title">
            <h1>{t.h}</h1>
            <p>{t.p}</p>
          </div>
          <HealthPill />
        </header>
        <div className="content">{children}</div>
      </div>
    </div>
  )
}

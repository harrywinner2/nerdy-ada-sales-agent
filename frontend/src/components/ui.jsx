// Small shared UI primitives.

export function Loading({ label = 'Loading…' }) {
  return (
    <div className="loading-wrap">
      <div className="spinner" />
      <div>{label}</div>
    </div>
  )
}

export function ErrorBanner({ message, onRetry }) {
  return (
    <div className="error-banner row between gap-12">
      <span>{message}</span>
      {onRetry && (
        <button className="btn" onClick={onRetry} style={{ padding: '6px 14px' }}>
          Retry
        </button>
      )}
    </div>
  )
}

export function Empty({ title, hint }) {
  return (
    <div className="empty fade-in">
      <div className="big">{title}</div>
      {hint && <div>{hint}</div>}
    </div>
  )
}

export function MiniBar({ value, color }) {
  const w = Math.max(0, Math.min(1, value || 0)) * 100
  return (
    <div className="minibar">
      <span style={{ width: `${w}%`, ...(color ? { background: color } : {}) }} />
    </div>
  )
}

export function SkeletonCard({ height = 120 }) {
  return <div className="skeleton" style={{ height, borderRadius: 20 }} />
}

const OUTCOME = {
  booked_consult: { cls: 'ok', label: 'Booked consult' },
  trial: { cls: 'ok', label: 'Trial started' },
  booked: { cls: 'ok', label: 'Booked' },
  not_now: { cls: 'dim', label: 'Not now' },
  disqualified: { cls: 'warn', label: 'Disqualified' },
  escalated: { cls: 'warn', label: 'Escalated' },
}
export function OutcomeChip({ outcome }) {
  const m = OUTCOME[outcome] || { cls: 'dim', label: outcome || 'open' }
  return <span className={`pill ${m.cls}`}>{m.label}</span>
}

const CHANNEL = {
  web: { cls: 'cyan', label: 'Web' },
  phone: { cls: 'violet', label: 'Phone' },
  sim: { cls: 'magenta', label: 'Simulated' },
  simulated: { cls: 'magenta', label: 'Simulated' },
}
export function ChannelChip({ channel }) {
  const m = CHANNEL[channel] || { cls: 'dim', label: channel || '—' }
  return <span className={`pill ${m.cls}`}>{m.label}</span>
}

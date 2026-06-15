import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useFetch } from '../lib/useFetch'
import { Loading, ErrorBanner, Empty, OutcomeChip, ChannelChip, MiniBar } from '../components/ui'
import { pct, shortTime, titleize } from '../lib/format'
import { IconBack, IconAsk, IconAnswer, IconClose, IconEscalate, IconDisqualify } from '../components/icons'

const ACTIONS = {
  ask: { color: 'var(--accent)', label: 'Ask', Icon: IconAsk },
  answer: { color: 'var(--accent-2)', label: 'Answer', Icon: IconAnswer },
  pivot_close: { color: 'var(--ok)', label: 'Pivot to close', Icon: IconClose },
  escalate: { color: 'var(--warn)', label: 'Escalate', Icon: IconEscalate },
  disqualify: { color: 'var(--bad)', label: 'Disqualify', Icon: IconDisqualify },
}

function ProfileBlock({ profile }) {
  if (!profile || typeof profile !== 'object') return <div className="faint">No profile gathered.</div>
  const entries = Object.entries(profile).filter(
    ([, v]) => v !== null && v !== undefined && v !== '' && !(Array.isArray(v) && !v.length)
  )
  if (!entries.length) return <div className="faint">No profile gathered.</div>
  return (
    <div className="profile-list">
      {entries.map(([k, v]) => (
        <div className="profile-row" key={k}>
          <span className="k">{titleize(k)}</span>
          <span className="val">{Array.isArray(v) ? v.join(', ') : String(v)}</span>
        </div>
      ))}
    </div>
  )
}

export default function CallDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { data, error, loading, reload } = useFetch(() => api.call(id), [id])

  if (loading) return <Loading label="Loading conversation…" />
  if (error) return <ErrorBanner message={error} onRetry={reload} />
  if (!data?.call) return <Empty title="Call not found" hint="It may have been removed." />

  const { call, turns = [], decisions = [], escalations = [], profile } = data
  const k = call.kpis || {}

  return (
    <div className="fade-in">
      <button className="btn" onClick={() => nav('/calls')} style={{ marginBottom: 18 }}>
        <IconBack style={{ width: 16, height: 16 }} /> Back to calls
      </button>

      <div className="card" style={{ marginBottom: 22 }}>
        <div className="row between wrap gap-12">
          <div className="row gap-12 wrap">
            <ChannelChip channel={call.channel} />
            <OutcomeChip outcome={call.outcome} />
            <span className="pill cyan">{call.version_tag || '—'}</span>
            <span className="muted" style={{ fontSize: 13 }}>
              {shortTime(call.started_at)}
            </span>
          </div>
          <div className="row gap-16 wrap" style={{ fontSize: 13 }}>
            <span className="muted">
              Discovery <b style={{ color: 'var(--text)' }}>{pct(k.discovery_completeness)}</b>
            </span>
            <span className="muted">
              Turns <b style={{ color: 'var(--text)' }}>{k.turns ?? '—'}</b>
            </span>
            <span className="muted">
              Decisions <b style={{ color: 'var(--text)' }}>{k.decisions ?? decisions.length}</b>
            </span>
            <span className="muted">
              Escalations <b style={{ color: 'var(--text)' }}>{k.escalations ?? escalations.length}</b>
            </span>
          </div>
        </div>
      </div>

      <div className="detail-grid">
        <div className="card">
          <div className="card-head">
            <h3>Transcript</h3>
            <span className="hint">{turns.length} turns</span>
          </div>
          {turns.length === 0 ? (
            <Empty title="No transcript" hint="This call has no recorded turns." />
          ) : (
            <div className="chat">
              {turns.map((t) => (
                <div key={t.idx} className={`bubble ${t.role === 'agent' ? 'agent' : 'prospect'}`}>
                  <div className="who">{t.role === 'agent' ? 'Ada' : 'Prospect'}</div>
                  {t.text}
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
          <div className="card">
            <div className="card-head">
              <h3>Decision timeline</h3>
              <span className="hint">why Ada acted</span>
            </div>
            {decisions.length === 0 ? (
              <div className="faint">No decision trace recorded.</div>
            ) : (
              <div className="timeline">
                {decisions.map((d, i) => {
                  const a = ACTIONS[d.action] || {
                    color: 'var(--text-dim)',
                    label: titleize(d.action),
                    Icon: IconAsk,
                  }
                  const Icon = a.Icon
                  return (
                    <div className="tl-item" key={i} style={{ color: a.color }}>
                      <span className="tl-node">
                        <Icon />
                      </span>
                      <div className="tl-head">
                        <span className="tl-action" style={{ color: 'var(--text)' }}>
                          {a.label}
                        </span>
                        {d.turn_index !== undefined && (
                          <span className="faint" style={{ fontSize: 11 }}>
                            turn {d.turn_index}
                          </span>
                        )}
                      </div>
                      {d.confidence !== undefined && d.confidence !== null && (
                        <div className="tl-conf">
                          <MiniBar value={d.confidence} color={a.color} />
                          <span className="v">{pct(d.confidence)} confidence</span>
                        </div>
                      )}
                      {d.rationale && <div className="tl-rationale">{d.rationale}</div>}
                      {Array.isArray(d.candidates) && d.candidates.length > 0 && (
                        <div className="candidates">
                          {d.candidates.map((c, j) => (
                            <div className="candidate" key={j}>
                              {c.field ? `${titleize(c.field)}` : ''}
                              {c.intent ? ` — ${c.intent}` : ''}
                              {c.required ? '  ·  required' : ''}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-head">
              <h3>Lead profile</h3>
            </div>
            <ProfileBlock profile={profile} />
          </div>

          {escalations.length > 0 && (
            <div className="card">
              <div className="card-head">
                <h3>Escalations</h3>
              </div>
              {escalations.map((e, i) => (
                <div key={i} className="row between" style={{ padding: '8px 0', borderTop: i ? '1px solid var(--line)' : 'none' }}>
                  <span style={{ fontSize: 13 }}>{e.reason}</span>
                  <span className={`pill ${e.severity === 'high' ? 'bad' : 'warn'}`}>
                    {e.severity || 'flag'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

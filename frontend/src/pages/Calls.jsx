import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useFetch } from '../lib/useFetch'
import { Loading, ErrorBanner, Empty, OutcomeChip, ChannelChip, MiniBar } from '../components/ui'
import { pct, relTime } from '../lib/format'

export default function Calls() {
  const nav = useNavigate()
  const { data, error, loading, reload } = useFetch(() => api.calls(), [])

  if (loading) return <Loading label="Loading calls…" />
  if (error) return <ErrorBanner message={error} onRetry={reload} />

  const calls = (data?.calls || []).slice().sort((a, b) => {
    const ta = new Date(a.started_at).getTime() || 0
    const tb = new Date(b.started_at).getTime() || 0
    return tb - ta
  })

  if (!calls.length)
    return (
      <Empty
        title="No calls yet"
        hint="Start one on the Live Call page or run an experiment to generate simulated calls."
      />
    )

  return (
    <div className="card fade-in" style={{ padding: '10px 8px' }}>
      <table className="calls-table">
        <thead>
          <tr>
            <th>Channel</th>
            <th>Outcome</th>
            <th>Discovery</th>
            <th>Turns</th>
            <th>Escalations</th>
            <th>Version</th>
            <th>When</th>
          </tr>
        </thead>
        <tbody>
          {calls.map((c) => {
            const k = c.kpis || {}
            return (
              <tr
                key={c.id}
                className="clickable"
                onClick={() => nav(`/calls/${c.id}`)}
              >
                <td>
                  <ChannelChip channel={c.channel} />
                </td>
                <td>
                  <OutcomeChip outcome={c.outcome} />
                </td>
                <td>
                  <div className="completeness-cell">
                    <MiniBar value={k.discovery_completeness} />
                    <span className="v">{pct(k.discovery_completeness)}</span>
                  </div>
                </td>
                <td className="muted">{k.turns ?? '—'}</td>
                <td className="muted">{k.escalations ?? 0}</td>
                <td>
                  <span className="pill cyan">{c.version_tag || '—'}</span>
                </td>
                <td className="muted">{relTime(c.started_at)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

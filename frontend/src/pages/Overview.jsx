import { api } from '../lib/api'
import { useFetch } from '../lib/useFetch'
import { Loading, ErrorBanner, Empty, MiniBar } from '../components/ui'
import { pct, num } from '../lib/format'

function Kpi({ label, value, sub, grad }) {
  return (
    <div className="card kpi-card">
      <div className="bar" />
      <div className="label">{label}</div>
      <div className={`value ${grad ? 'grad' : ''}`}>{value}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  )
}

export default function Overview() {
  const { data, error, loading, reload } = useFetch(() => api.overview(), [])
  if (loading) return <Loading label="Loading performance…" />
  if (error) return <ErrorBanner message={error} onRetry={reload} />

  const agg = data?.aggregate || {}
  const versions = data?.versions || []

  if (!agg.calls && !versions.length)
    return (
      <Empty
        title="No performance data yet"
        hint="Run an experiment or take some live calls to populate KPIs."
      />
    )

  const maxClose = Math.max(0.0001, ...versions.map((v) => v.close_rate || 0))

  return (
    <div className="fade-in">
      <div className="kpi-grid">
        <Kpi label="Close rate" value={pct(agg.close_rate)} grad sub="booked consult or trial" />
        <Kpi label="Avg discovery completeness" value={pct(agg.avg_completeness)} sub="qualifying facts gathered" />
        <Kpi label="Total calls" value={num(agg.calls)} sub="across all versions" />
        <Kpi label="Disqualified rate" value={pct(agg.disqualified_rate)} sub="correctly screened out" />
        <Kpi label="Escalation rate" value={pct(agg.escalation_rate)} sub="handed to a human" />
        <Kpi label="Avg turns" value={agg.avg_turns != null ? agg.avg_turns.toFixed(1) : '—'} sub="conversation length" />
      </div>

      <div className="card" style={{ marginTop: 22 }}>
        <div className="card-head">
          <h3>Performance by version</h3>
          <span className="hint">each promotion should move the line</span>
        </div>
        {versions.length === 0 ? (
          <div className="faint">No versioned data yet.</div>
        ) : (
          <table className="ver-table">
            <thead>
              <tr>
                <th>Version</th>
                <th className="num">Calls</th>
                <th className="num">Completeness</th>
                <th className="num">Disqualified</th>
                <th className="num">Escalation</th>
                <th className="num">Avg turns</th>
                <th style={{ width: 200 }}>Close rate</th>
              </tr>
            </thead>
            <tbody>
              {versions.map((v) => (
                <tr key={v.version_tag}>
                  <td>
                    <span className="pill cyan">{v.version_tag}</span>
                  </td>
                  <td className="num muted">{num(v.calls)}</td>
                  <td className="num muted">{pct(v.avg_completeness)}</td>
                  <td className="num muted">{pct(v.disqualified_rate)}</td>
                  <td className="num muted">{pct(v.escalation_rate)}</td>
                  <td className="num muted">{v.avg_turns != null ? v.avg_turns.toFixed(1) : '—'}</td>
                  <td>
                    <div className="bar-cell">
                      <MiniBar value={(v.close_rate || 0) / maxClose} />
                      <b style={{ width: 44, textAlign: 'right' }}>{pct(v.close_rate)}</b>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

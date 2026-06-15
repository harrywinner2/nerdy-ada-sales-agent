import { api } from '../lib/api'
import { useFetch } from '../lib/useFetch'
import { Loading, ErrorBanner, Empty } from '../components/ui'

function initials(label) {
  return (label || '?')
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
}

export default function Personas() {
  const { data, error, loading, reload } = useFetch(() => api.personas(), [])
  if (loading) return <Loading label="Loading synthetic prospects…" />
  if (error) return <ErrorBanner message={error} onRetry={reload} />

  const prospects = data?.prospects || []
  if (!prospects.length) return <Empty title="No personas defined" />

  return (
    <div className="fade-in">
      <p className="lead" style={{ marginTop: 0, maxWidth: 760 }}>
        Ada is stress-tested against these adversarial personas — honest, non-obedient prospects
        engineered to resist the script: skeptics, budget objectors, off-topic ramblers, and
        out-of-ICP leads who should be disqualified. If the agent can hold up here, it holds up
        with real buyers.
      </p>

      <div className="persona-grid">
        {prospects.map((p) => (
          <div className="card persona-card glass" key={p.key}>
            <div className="row between gap-12">
              <div className="row gap-12">
                <div className="avatar">{initials(p.label)}</div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{p.label}</div>
                  <div className="faint mono" style={{ fontSize: 11, marginTop: 2 }}>
                    {p.key}
                  </div>
                </div>
              </div>
              <span className={`pill ${p.fit === 'in_icp' ? 'ok' : 'warn'}`}>
                {p.fit === 'in_icp' ? 'In ICP' : 'Out of ICP'}
              </span>
            </div>
            <p className="p-brief">{p.brief}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

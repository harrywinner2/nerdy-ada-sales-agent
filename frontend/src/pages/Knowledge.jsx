import { useMemo, useState } from 'react'
import { api } from '../lib/api'
import { useFetch } from '../lib/useFetch'
import { Loading, ErrorBanner, Empty } from '../components/ui'
import { IconSearch } from '../components/icons'
import { titleize } from '../lib/format'

const CATS = ['policy', 'objection', 'competitive', 'pricing', 'product']

function DocCard({ doc }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="card kb-card glass" onClick={() => setOpen((o) => !o)}>
      <span className={`tag cat-${doc.category}`}>{titleize(doc.category)}</span>
      <div className="doc-title">{doc.title}</div>
      <div className={`doc-body ${open ? '' : 'clamped'}`}>{doc.content}</div>
      <div className="faint" style={{ fontSize: 11, marginTop: 10 }}>
        {open ? 'Click to collapse' : 'Click to read'}
      </div>
    </div>
  )
}

export default function Knowledge() {
  const { data, error, loading, reload } = useFetch(() => api.knowledge(), [])
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('all')

  const docs = data?.docs || []
  const filtered = useMemo(() => {
    const ql = q.trim().toLowerCase()
    return docs.filter((d) => {
      if (cat !== 'all' && d.category !== cat) return false
      if (!ql) return true
      return (
        (d.title || '').toLowerCase().includes(ql) ||
        (d.content || '').toLowerCase().includes(ql) ||
        (d.category || '').toLowerCase().includes(ql)
      )
    })
  }, [docs, q, cat])

  if (loading) return <Loading label="Loading knowledge base…" />
  if (error) return <ErrorBanner message={error} onRetry={reload} />

  return (
    <div className="fade-in">
      <p className="lead" style={{ marginTop: 0, maxWidth: 720 }}>
        These documents are Ada's only source of truth. She grounds every answer here — pricing,
        policies, competitive positioning — so the agent never invents facts.
      </p>

      <div className="kb-toolbar">
        <div className="kb-search" style={{ position: 'relative', flex: 1 }}>
          <IconSearch
            style={{ width: 16, height: 16, position: 'absolute', left: 13, top: 13, color: 'var(--text-faint)' }}
          />
          <input
            className="input"
            style={{ paddingLeft: 38 }}
            placeholder="Search documents…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <div className="cat-filter">
          <button
            className={`pill ${cat === 'all' ? 'cyan' : ''}`}
            onClick={() => setCat('all')}
            style={{ cursor: 'pointer' }}
          >
            All ({docs.length})
          </button>
          {CATS.map((c) => {
            const n = docs.filter((d) => d.category === c).length
            if (!n) return null
            return (
              <button
                key={c}
                className={`pill ${cat === c ? 'cyan' : ''}`}
                onClick={() => setCat(c)}
                style={{ cursor: 'pointer' }}
              >
                {titleize(c)} ({n})
              </button>
            )
          })}
        </div>
      </div>

      {filtered.length === 0 ? (
        <Empty title="No documents match" hint="Try a different search term or category." />
      ) : (
        <div className="kb-grid">
          {filtered.map((d) => (
            <DocCard key={d.id} doc={d} />
          ))}
        </div>
      )}
    </div>
  )
}

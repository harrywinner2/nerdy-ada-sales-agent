// Formatting helpers.

export function pct(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${(value * 100).toFixed(digits)}%`
}

export function num(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat().format(value)
}

export function relTime(ts) {
  if (!ts) return '—'
  const d = typeof ts === 'number' ? new Date(ts * (ts < 1e12 ? 1000 : 1)) : new Date(ts)
  if (Number.isNaN(d.getTime())) return '—'
  const diff = (Date.now() - d.getTime()) / 1000
  if (diff < 45) return 'just now'
  if (diff < 90) return '1 min ago'
  if (diff < 3600) return `${Math.round(diff / 60)} min ago`
  if (diff < 5400) return '1 hr ago'
  if (diff < 86400) return `${Math.round(diff / 3600)} hr ago`
  if (diff < 172800) return 'yesterday'
  if (diff < 604800) return `${Math.round(diff / 86400)} days ago`
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function shortTime(ts) {
  if (!ts) return '—'
  const d = typeof ts === 'number' ? new Date(ts * (ts < 1e12 ? 1000 : 1)) : new Date(ts)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function titleize(s) {
  if (!s) return ''
  return String(s)
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

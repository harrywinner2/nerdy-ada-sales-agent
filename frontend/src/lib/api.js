// Tiny fetch helpers for the Ada backend API.
// All calls go through our backend — never directly to OpenAI.

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    let detail = ''
    try {
      const j = await res.json()
      detail = j.error || j.detail || JSON.stringify(j)
    } catch {
      detail = await res.text().catch(() => '')
    }
    const err = new Error(detail || `Request failed (${res.status})`)
    err.status = res.status
    throw err
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  health: () => request('/api/health'),
  overview: () => request('/api/overview'),
  calls: () => request('/api/calls'),
  call: (id) => request(`/api/calls/${encodeURIComponent(id)}`),
  knowledge: () => request('/api/knowledge'),
  personas: () => request('/api/personas'),
  experiments: () => request('/api/experiments'),
  runExperiment: (body) =>
    request('/api/experiments/run', { method: 'POST', body: JSON.stringify(body || {}) }),
  dial: (to) =>
    request('/twilio/dial', { method: 'POST', body: JSON.stringify({ to }) }),
}

export default api

// Hand-rolled grouped SVG bar chart. No chart libraries.
// series: [{ key, label, color }]
// rows: [{ label, values: { [key]: number 0..1 } }]
export default function BarChart({ rows, series, height = 220 }) {
  if (!rows || !rows.length) return null
  const pad = { top: 16, right: 12, bottom: 38, left: 38 }
  const W = 640
  const H = height
  const chartW = W - pad.left - pad.right
  const chartH = H - pad.top - pad.bottom
  const groupW = chartW / rows.length
  const barGap = 8
  const barW = (groupW - barGap * (series.length + 1)) / series.length

  const ticks = [0, 0.25, 0.5, 0.75, 1]

  return (
    <div className="barchart">
      <div className="bc-legend">
        {series.map((s) => (
          <span key={s.key}>
            <i style={{ background: s.color }} />
            {s.label}
          </span>
        ))}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="comparison chart">
        {ticks.map((t) => {
          const y = pad.top + chartH - t * chartH
          return (
            <g key={t}>
              <line
                x1={pad.left}
                x2={W - pad.right}
                y1={y}
                y2={y}
                stroke="rgba(255,255,255,0.07)"
                strokeWidth="1"
              />
              <text x={pad.left - 8} y={y + 4} fontSize="10" textAnchor="end" fill="rgba(255,255,255,0.4)">
                {Math.round(t * 100)}%
              </text>
            </g>
          )
        })}
        {rows.map((row, i) => {
          const gx = pad.left + i * groupW
          return (
            <g key={row.label}>
              {series.map((s, j) => {
                const v = Math.max(0, Math.min(1, row.values[s.key] || 0))
                const bh = v * chartH
                const x = gx + barGap + j * (barW + barGap)
                const y = pad.top + chartH - bh
                return (
                  <g key={s.key}>
                    <rect
                      x={x}
                      y={y}
                      width={barW}
                      height={bh}
                      rx="4"
                      fill={s.color}
                      opacity="0.92"
                    >
                      <title>{`${row.label} · ${s.label}: ${Math.round(v * 100)}%`}</title>
                    </rect>
                    <text
                      x={x + barW / 2}
                      y={y - 6}
                      fontSize="10"
                      textAnchor="middle"
                      fill="rgba(255,255,255,0.7)"
                    >
                      {Math.round(v * 100)}%
                    </text>
                  </g>
                )
              })}
              <text
                x={gx + groupW / 2}
                y={H - 14}
                fontSize="11"
                textAnchor="middle"
                fill="rgba(255,255,255,0.64)"
              >
                {row.label.length > 18 ? row.label.slice(0, 17) + '…' : row.label}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

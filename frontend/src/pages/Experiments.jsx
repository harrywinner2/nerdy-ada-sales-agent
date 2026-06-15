import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { Loading, ErrorBanner, Empty } from '../components/ui'
import BarChart from '../components/BarChart'
import { pct, shortTime, titleize } from '../lib/format'

const DECISIONS = {
  auto_promoted: { cls: 'ok', label: 'Auto-promoted' },
  promoted_with_review: { cls: 'cyan', label: 'Promoted with review' },
  escalated_no_promote: { cls: 'warn', label: 'Escalated — no promote' },
  kept_baseline: { cls: 'dim', label: 'Kept baseline' },
}

const RUN_MESSAGES = [
  'Spinning up synthetic prospects…',
  'Drafting candidate strategies…',
  'Running adversarial conversations…',
  'An LLM judge is scoring each transcript…',
  'Comparing close rates and objection handling…',
  'Deciding whether to promote a winner…',
]

const VARIANT_STATUS = {
  baseline: 'dim',
  candidate: 'violet',
  promoted: 'ok',
  retired: 'warn',
}

function Arm({ arm, isWinner }) {
  const [openSample, setOpenSample] = useState(false)
  const s = arm.scores || {}
  const sample = (arm.sample && arm.sample[0]) || null
  return (
    <div className={`arm ${arm.is_baseline ? 'baseline' : ''} ${isWinner ? 'promoted' : ''}`}>
      <div className="arm-head">
        <div className="row gap-8 wrap">
          <b style={{ fontSize: 14 }}>{arm.label}</b>
          {arm.is_baseline && <span className="pill dim">baseline</span>}
          {isWinner && <span className="pill ok">winner</span>}
        </div>
        <span className="pill cyan">{pct(s.close_rate)} close</span>
      </div>
      {arm.text && <div className="arm-strategy">{arm.text}</div>}
      <div className="arm-scores">
        <span className="s">calls <b>{s.calls ?? '—'}</b></span>
        <span className="s">objections resolved <b>{pct(s.objection_resolution)}</b></span>
        <span className="s">completeness <b>{pct(s.avg_completeness)}</b></span>
        <span className="s">disqualified <b>{pct(s.disqualified)}</b></span>
        <span className="s">realism <b>{pct(s.realism)}</b></span>
      </div>
      {sample && (
        <>
          <button className="sample-toggle" onClick={() => setOpenSample((o) => !o)}>
            {openSample ? '▾ Hide sample transcript' : '▸ Show sample transcript'}
          </button>
          {openSample && (
            <div className="sample">
              {sample.judged && (
                <div className="judge">
                  <b>Judge:</b>{' '}
                  {sample.judged.converted ? 'converted · ' : ''}
                  {sample.judged.disqualified ? 'disqualified · ' : ''}
                  {sample.judged.walked ? 'walked · ' : ''}
                  {sample.judged.price_objection_raised
                    ? sample.judged.price_objection_resolved
                      ? 'price objection resolved · '
                      : 'price objection unresolved · '
                    : ''}
                  realism {pct(sample.judged.realism)}
                  {sample.judged.note ? ` — ${sample.judged.note}` : ''}
                </div>
              )}
              {sample.prospect && (
                <div className="faint mono" style={{ fontSize: 11, marginBottom: 10 }}>
                  prospect: {sample.prospect}
                </div>
              )}
              {(sample.transcript || []).map((m, i) => {
                const role = m.role === 'assistant' || m.role === 'agent' ? 'assistant' : 'user'
                return (
                  <div key={i} className={`sample-line ${role}`}>
                    <span className="r">{role === 'assistant' ? 'Ada: ' : 'Prospect: '}</span>
                    {m.content}
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function ExperimentBlock({ exp }) {
  const dec = DECISIONS[exp.decision] || { cls: 'dim', label: titleize(exp.decision) }
  const delta = exp.delta_close_rate || 0
  const deltaCls = delta > 0.0001 ? 'pos' : delta < -0.0001 ? 'neg' : 'zero'
  const arms = exp.arms || []
  const baseArm = arms.find((a) => a.is_baseline)
  const winnerId = exp.winner?.id

  const rows = arms.map((a) => ({
    label: a.label,
    values: {
      close: a.scores?.close_rate || 0,
      obj: a.scores?.objection_resolution || 0,
    },
  }))
  const series = [
    { key: 'close', label: 'Close rate', color: '#17E2EA' },
    { key: 'obj', label: 'Objection resolution', color: '#8B5CFF' },
  ]

  return (
    <div className="card exp-block fade-in">
      <div className="exp-top">
        <div>
          <div className="dim">{titleize(exp.dimension)} experiment</div>
          <h3>{exp.winner?.label || 'Winner'}</h3>
        </div>
        <span className={`decision-badge pill ${dec.cls}`}>{dec.label}</span>
      </div>

      <div className="beforeafter" style={{ marginBottom: 24 }}>
        <div className="ba-cell">
          <div className="lab">Before · baseline</div>
          <div className="big">{pct(exp.baseline_close_rate)}</div>
          <div className="name">{baseArm?.label || 'baseline'}</div>
        </div>
        <span className="ba-arrow">→</span>
        <div className="ba-cell winner">
          <div className="lab">After · winner</div>
          <div className="big" style={{ color: 'var(--ok)' }}>{pct(exp.winner_close_rate)}</div>
          <div className="name">{exp.winner?.label}{exp.winner?.is_baseline ? ' (baseline kept)' : ''}</div>
        </div>
        <div className={`delta-chip ${deltaCls}`}>
          <span className="big">{delta >= 0 ? '+' : ''}{pct(delta)}</span>
          <span className="lab">close rate delta</span>
        </div>
      </div>

      {rows.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <BarChart rows={rows} series={series} />
        </div>
      )}

      <div className="card-head" style={{ marginTop: 6 }}>
        <h3 style={{ fontSize: 14 }}>Arms</h3>
        <span className="hint">strategy text + judged samples</span>
      </div>
      {arms.map((a) => (
        <Arm key={a.id} arm={a} isWinner={a.id === winnerId && !a.is_baseline} />
      ))}
    </div>
  )
}

export default function Experiments() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [seeds, setSeeds] = useState(6)
  const [variantCount, setVariantCount] = useState(2)
  const [running, setRunning] = useState(false)
  const [msgIdx, setMsgIdx] = useState(0)
  const [runErr, setRunErr] = useState(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setData(await api.experiments())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => {
    load()
  }, [])

  useEffect(() => {
    if (!running) return
    const id = setInterval(() => setMsgIdx((i) => (i + 1) % RUN_MESSAGES.length), 4000)
    return () => clearInterval(id)
  }, [running])

  async function run() {
    setRunning(true)
    setRunErr(null)
    setMsgIdx(0)
    try {
      await api.runExperiment({ seeds: Number(seeds) || undefined, variant_count: Number(variantCount) || undefined })
      await load()
    } catch (e) {
      setRunErr(e.message || 'Experiment failed')
    } finally {
      setRunning(false)
    }
  }

  const experiments = data?.experiments || []
  const variants = data?.variants || []

  return (
    <div className="fade-in">
      <div className="card" style={{ marginBottom: 22 }}>
        <div className="card-head">
          <h3>Run a new experiment</h3>
          <span className="hint">Ada improves itself against synthetic prospects</span>
        </div>
        <p className="lead" style={{ marginTop: 0, maxWidth: 720 }}>
          Generate candidate strategy variants, run them against adversarial prospects, score every
          transcript with an LLM judge, and promote a winner only when it beats the baseline.
        </p>
        <div className="exp-runner">
          <div className="fld">
            <label className="field-label">Seeds (prospects)</label>
            <input
              className="input"
              type="number"
              min="1"
              max="20"
              value={seeds}
              onChange={(e) => setSeeds(e.target.value)}
              disabled={running}
            />
          </div>
          <div className="fld">
            <label className="field-label">Variant count</label>
            <input
              className="input"
              type="number"
              min="1"
              max="6"
              value={variantCount}
              onChange={(e) => setVariantCount(e.target.value)}
              disabled={running}
            />
          </div>
          <button className="btn primary" onClick={run} disabled={running}>
            {running ? 'Running…' : 'Run experiment'}
          </button>
        </div>
        {running && (
          <div className="run-status">
            <div className="spinner" />
            <div className="txt">
              <b>Recursive improvement in progress</b>
              <span>{RUN_MESSAGES[msgIdx]} This usually takes 1–3 minutes.</span>
            </div>
          </div>
        )}
        {runErr && (
          <div className="error-banner" style={{ marginTop: 16 }}>
            {runErr}
          </div>
        )}
      </div>

      {variants.length > 0 && (
        <div className="card" style={{ marginBottom: 22 }}>
          <div className="card-head">
            <h3>Strategy variants</h3>
            <span className="hint">{variants.length} tracked</span>
          </div>
          {variants.map((v) => (
            <div className="variant-row" key={v.id}>
              <div>
                <div className="vdim">{titleize(v.dimension)}</div>
                <div className="vtext">{v.label || v.text}</div>
                {v.text && v.label && (
                  <div className="faint mono" style={{ fontSize: 11, marginTop: 4 }}>
                    {v.text.length > 120 ? v.text.slice(0, 119) + '…' : v.text}
                  </div>
                )}
              </div>
              <div className="row gap-12" style={{ flexShrink: 0 }}>
                <span className="faint" style={{ fontSize: 11 }}>{v.created_at ? shortTime(v.created_at) : ''}</span>
                <span className={`pill ${VARIANT_STATUS[v.status] || 'dim'}`}>{titleize(v.status)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <Loading label="Loading experiments…" />
      ) : error ? (
        <ErrorBanner message={error} onRetry={load} />
      ) : experiments.length === 0 ? (
        <Empty
          title="No experiments yet"
          hint="Run your first experiment above to watch Ada try to beat her own baseline."
        />
      ) : (
        experiments.map((exp) => <ExperimentBlock key={exp.experiment_id} exp={exp} />)
      )}
    </div>
  )
}

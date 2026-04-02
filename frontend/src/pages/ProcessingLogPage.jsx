import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

function fmt(n, dec = 0) {
  if (n == null) return '—'
  return Number(n).toLocaleString('en-EU', { minimumFractionDigits: dec, maximumFractionDigits: dec })
}

const VERDICT_STYLE = {
  incorrect: { background: '#fde8e8', color: 'var(--error)',   label: '✗ Incorrect' },
  correct:   { background: '#d4edda', color: 'var(--success)', label: '✓ Correct'   },
  uncertain: { background: '#fff3cd', color: '#856404',        label: '? Uncertain'  },
}

function VerdictBadge({ verdict }) {
  const s = VERDICT_STYLE[verdict] || VERDICT_STYLE.uncertain
  return (
    <span style={{
      background: s.background, color: s.color,
      padding: '2px 10px', borderRadius: 10, fontSize: 11, fontWeight: 700,
      whiteSpace: 'nowrap',
    }}>
      {s.label}
    </span>
  )
}

function ReasoningCell({ text }) {
  const [expanded, setExpanded] = useState(false)
  const SHORT_LEN = 120

  if (!text) return <span style={{ color: 'var(--text-muted)' }}>—</span>

  if (text.length <= SHORT_LEN) return <span>{text}</span>

  return (
    <span>
      {expanded ? text : text.slice(0, SHORT_LEN) + '…'}
      {' '}
      <button
        onClick={() => setExpanded(e => !e)}
        style={{
          background: 'none', border: 'none', color: 'var(--primary)',
          cursor: 'pointer', fontSize: 11, padding: 0, fontWeight: 600,
        }}
      >
        {expanded ? 'Show less' : 'Show more'}
      </button>
    </span>
  )
}

export default function ProcessingLogPage() {
  const [items, setItems]     = useState([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats]     = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const res = await axios.get('/api/agent-log?limit=200')
      const data = res.data
      setItems(data)
      // Compute quick stats
      const total     = data.length
      const incorrect = data.filter(r => r.verdict === 'incorrect').length
      const correct   = data.filter(r => r.verdict === 'correct').length
      const uncertain = data.filter(r => r.verdict === 'uncertain').length
      setStats({ total, incorrect, correct, uncertain })
    } catch { /* ignore */ }
    setLoading(false)
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 5000)
    return () => clearInterval(id)
  }, [refresh])

  return (
    <div className="page-container">
      <div className="page-title">Agent Processing Log</div>
      <div className="page-subtitle">
        VAT fraud detection agent analysis — suspicious Ireland-bound transactions
      </div>

      {/* Stats row */}
      {stats && (
        <div className="metrics-row" style={{ marginBottom: 20 }}>
          <div className="metric-tile">
            <div className="metric-tile__label">Total processed</div>
            <div className="metric-tile__value">{stats.total}</div>
            <div className="metric-tile__sub">by agent</div>
          </div>
          <div className="metric-tile error-tile">
            <div className="metric-tile__label">Incorrect</div>
            <div className="metric-tile__value">{stats.incorrect}</div>
            <div className="metric-tile__sub">sent to Ireland queue</div>
          </div>
          <div className="metric-tile">
            <div className="metric-tile__label" style={{ color: 'var(--success)' }}>Correct</div>
            <div className="metric-tile__value">{stats.correct}</div>
            <div className="metric-tile__sub">cleared</div>
          </div>
          <div className="metric-tile">
            <div className="metric-tile__label">Uncertain</div>
            <div className="metric-tile__value">{stats.uncertain}</div>
            <div className="metric-tile__sub">cleared</div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <span>Processing History</span>
          {loading && <span className="text-muted" style={{ fontSize: 11 }}>Refreshing…</span>}
        </div>

        {items.length === 0 ? (
          <div className="alarms-empty">
            <div className="alarms-empty__icon">🤖</div>
            <div className="alarms-empty__text">
              No transactions processed yet. The agent will analyse suspicious
              Ireland-bound transactions as they arrive.
              <br />
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Scenario: TechZone GmbH → IE alarm fires during week 2 of March 2026.
              </span>
            </div>
          </div>
        ) : (
          <div className="tx-table-wrap">
            <table className="tx-table">
              <thead>
                <tr>
                  <th>Processed at</th>
                  <th>Seller</th>
                  <th>To</th>
                  <th>Item</th>
                  <th style={{ textAlign: 'right' }}>Value (€)</th>
                  <th style={{ textAlign: 'right' }}>Applied VAT</th>
                  <th style={{ textAlign: 'right' }}>Correct VAT</th>
                  <th>Verdict</th>
                  <th>Forwarded</th>
                  <th style={{ minWidth: 260 }}>Agent reasoning</th>
                </tr>
              </thead>
              <tbody>
                {items.map(r => (
                  <tr key={r.id} style={{
                    background: r.verdict === 'incorrect' ? '#fff8f8'
                               : r.verdict === 'correct'  ? '#f6fff8'
                               : '#fffdf0',
                  }}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: 11 }}>
                      {r.processed_at?.slice(0, 16).replace('T', ' ')}
                    </td>
                    <td style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {r.seller_name}
                    </td>
                    <td><span className="badge country">{r.buyer_country}</span></td>
                    <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {r.item_description}
                    </td>
                    <td style={{ textAlign: 'right' }}>{fmt(r.value, 2)}</td>
                    <td style={{ textAlign: 'right', color: 'var(--error)', fontWeight: 700 }}>
                      {(r.vat_rate * 100).toFixed(1)}%
                    </td>
                    <td style={{ textAlign: 'right', color: 'var(--success)' }}>
                      {(r.correct_vat_rate * 100).toFixed(1)}%
                    </td>
                    <td><VerdictBadge verdict={r.verdict} /></td>
                    <td style={{ textAlign: 'center' }}>
                      {r.sent_to_ireland
                        ? <span className="badge err">→ IE</span>
                        : <span className="badge ok">Cleared</span>}
                    </td>
                    <td style={{ fontSize: 11, color: 'var(--text-secondary)', maxWidth: 300 }}>
                      <ReasoningCell text={r.reasoning} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

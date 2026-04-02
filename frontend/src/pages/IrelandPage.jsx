import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

function fmt(n, dec = 0) {
  if (n == null) return '—'
  return Number(n).toLocaleString('en-EU', { minimumFractionDigits: dec, maximumFractionDigits: dec })
}

function ReasoningCell({ text }) {
  const [expanded, setExpanded] = useState(false)
  const SHORT_LEN = 140

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

function AlarmContext({ item }) {
  return (
    <div style={{
      fontSize: 11, color: 'var(--text-secondary)',
      display: 'flex', flexDirection: 'column', gap: 2,
    }}>
      <div>
        <span style={{ color: 'var(--text-muted)' }}>Alarm: </span>
        <strong style={{ color: 'var(--error)' }}>{item.alarm_key}</strong>
      </div>
      {item.deviation_pct != null && (
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Ratio deviation: </span>
          <strong style={{ color: 'var(--error)' }}>+{fmt(item.deviation_pct, 1)}%</strong>
          {' '}
          <span style={{ color: 'var(--text-muted)' }}>
            ({fmt(item.ratio_current * 100, 2)}% current vs {fmt(item.ratio_historical * 100, 2)}% historical)
          </span>
        </div>
      )}
    </div>
  )
}

export default function IrelandPage() {
  const [items, setItems]     = useState([])
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const res = await axios.get('/api/ireland-queue?limit=200')
      setItems(res.data)
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
      {/* IE flag strip */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        marginBottom: 4,
      }}>
        <span style={{ fontSize: 32 }}>🇮🇪</span>
        <div>
          <div className="page-title" style={{ marginBottom: 0 }}>Ireland Investigation Queue</div>
          <div className="page-subtitle" style={{ marginTop: 2 }}>
            Transactions confirmed incorrect by the VAT fraud detection agent — forwarded for local investigation
          </div>
        </div>
      </div>

      {/* Summary banner */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16,
        background: items.length ? '#fff8f8' : '#f6fff8',
        border: `1px solid ${items.length ? '#f5c6cb' : '#c3e6cb'}`,
        borderLeft: `4px solid ${items.length ? 'var(--error)' : 'var(--success)'}`,
        borderRadius: 'var(--radius)',
        padding: '12px 16px',
        marginBottom: 20,
        boxShadow: 'var(--shadow)',
      }}>
        <div style={{ fontSize: 24 }}>{items.length ? '⚠' : '✓'}</div>
        <div>
          <div style={{
            fontWeight: 700,
            color: items.length ? 'var(--error)' : 'var(--success)',
            fontSize: 14,
          }}>
            {items.length
              ? `${items.length} transaction${items.length > 1 ? 's' : ''} pending local investigation`
              : 'No transactions in the investigation queue'}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
            These transactions were flagged by a VAT ratio alarm <strong>and</strong> confirmed
            incorrect by the AI agent (suspicion level: <strong style={{ color: 'var(--error)' }}>HIGH</strong>).
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span>Investigation Queue</span>
          {loading && <span className="text-muted" style={{ fontSize: 11 }}>Refreshing…</span>}
        </div>

        {items.length === 0 ? (
          <div className="alarms-empty">
            <div className="alarms-empty__icon">🔍</div>
            <div className="alarms-empty__text">
              No transactions have been forwarded to the Ireland investigation queue yet.
              <br />
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Transactions appear here when: (1) a VAT ratio alarm is active for an
                Ireland-bound supplier, and (2) the AI agent confirms the VAT rate is incorrect.
              </span>
            </div>
          </div>
        ) : (
          <div className="tx-table-wrap">
            <table className="tx-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Seller</th>
                  <th>From</th>
                  <th>Item</th>
                  <th style={{ textAlign: 'right' }}>Value (€)</th>
                  <th style={{ textAlign: 'right' }}>Applied VAT</th>
                  <th style={{ textAlign: 'right' }}>Correct VAT</th>
                  <th style={{ textAlign: 'right' }}>VAT Due (€)</th>
                  <th>Suspicion</th>
                  <th style={{ minWidth: 200 }}>Alarm context</th>
                  <th style={{ minWidth: 260 }}>Agent reasoning</th>
                </tr>
              </thead>
              <tbody>
                {items.map(r => (
                  <tr key={r.id} style={{ background: '#fff8f8' }}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: 11 }}>
                      {r.transaction_date?.slice(0, 16).replace('T', ' ')}
                    </td>
                    <td style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      <span style={{ color: 'var(--error)', marginRight: 4 }}>⚠</span>
                      {r.seller_name}
                    </td>
                    <td><span className="badge country">{r.seller_country}</span></td>
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
                    <td style={{ textAlign: 'right', fontWeight: 700 }}>
                      {fmt(r.vat_amount, 2)}
                    </td>
                    <td>
                      <span style={{
                        background: '#fde8e8', color: 'var(--error)',
                        padding: '2px 10px', borderRadius: 10,
                        fontSize: 11, fontWeight: 700,
                      }}>
                        HIGH
                      </span>
                    </td>
                    <td><AlarmContext item={r} /></td>
                    <td style={{ fontSize: 11, color: 'var(--text-secondary)', maxWidth: 300 }}>
                      <ReasoningCell text={r.agent_reasoning} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Legend */}
      <div style={{
        marginTop: 16, padding: '12px 16px',
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius)', fontSize: 12, color: 'var(--text-secondary)',
      }}>
        <strong>How transactions reach this queue:</strong>
        {' '}A VAT ratio deviation alarm fires for a supplier → Ireland pair (7-day ratio
        deviates &gt;25% from 8-week baseline) → each new transaction from that pair is flagged
        as suspicious (suspicion level: <em>medium</em>) → the AI agent analyses the transaction
        → if the verdict is <strong style={{ color: 'var(--error)' }}>incorrect</strong>, the
        suspicion level is upgraded to <strong style={{ color: 'var(--error)' }}>high</strong>{' '}
        and the transaction is forwarded here for local investigation.
      </div>
    </div>
  )
}

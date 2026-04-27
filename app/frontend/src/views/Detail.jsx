import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client.js'
import {
  IconTarget, IconUtensils, IconClock, IconDollar, MS,
} from '../components/Icons.jsx'

// Map a 1-5 rounded score to a Material Symbols sentiment glyph name.
const SENTIMENT_BY_ROUND = {
  1: 'sentiment_extremely_dissatisfied',
  2: 'sentiment_frustrated',
  3: 'sentiment_neutral',
  4: 'sentiment_satisfied',
  5: 'sentiment_very_satisfied',
}
function sentimentName(scoreFive) {
  if (scoreFive == null) return null
  const r = Math.max(1, Math.min(5, Math.round(scoreFive)))
  return SENTIMENT_BY_ROUND[r]
}

const WEEKDAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

// Parse whatever Google hours format comes back. Two known shapes:
//   A) "Monday11AM–10PM" / "FridayClosed"         — concatenated
//   B) "['Monday' '10AM–10PM']" / "['Friday' 'Closed']" — numpy-array repr
// Returns [{day, open, close, closed}] in canonical Mon→Sun order.
function parseHours(list) {
  if (!Array.isArray(list)) return []
  const byDay = {}
  for (const raw of list) {
    if (typeof raw !== 'string') continue
    let dayToken = null, timeToken = null

    // Shape B: literal numpy repr
    const mB = raw.match(/\[\s*'([^']+)'\s+'([^']+)'\s*\]/)
    if (mB) {
      dayToken  = mB[1].trim()
      timeToken = mB[2].trim()
    } else {
      // Shape A: Day directly prefixed
      const day = WEEKDAY_ORDER.find(d => raw.startsWith(d))
      if (!day) continue
      dayToken  = day
      timeToken = raw.slice(day.length).trim()
    }

    if (!WEEKDAY_ORDER.includes(dayToken)) continue
    if (/closed/i.test(timeToken)) {
      byDay[dayToken] = { day: dayToken, closed: true }
      continue
    }
    const parts = timeToken.split('–')
    if (parts.length !== 2) {
      byDay[dayToken] = { day: dayToken, raw: timeToken }
      continue
    }
    byDay[dayToken] = { day: dayToken, open: parts[0].trim(), close: parts[1].trim() }
  }
  return WEEKDAY_ORDER.filter(d => byDay[d]).map(d => byDay[d])
}

function formatValue(v) {
  if (v == null) return '-'
  if (typeof v === 'string' && !v.trim()) return '-'
  if (Array.isArray(v)) return v.length === 0 ? '-' : v.join(', ')
  if (typeof v === 'object') return Object.keys(v).length === 0 ? '-' : JSON.stringify(v)
  return String(v)
}

function ReviewPhoto({ url }) {
  const [failed, setFailed] = useState(false)
  if (failed || !url) {
    return <div className="review-photo placeholder">no photo</div>
  }
  return (
    <img className="review-photo" src={url} alt="" loading="lazy" onError={() => setFailed(true)} />
  )
}

function formatTime(ms) {
  if (!ms) return ''
  try {
    const d = new Date(Number(ms))
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch { return '' }
}

export default function Detail({ gmapId, lastSearchScore, onBack, variant = 'page', closeLabel = '← Back' }) {
  const [detail,  setDetail]  = useState(null)
  const [page,    setPage]    = useState(1)
  const [reviews, setReviews] = useState(null)
  const [err,     setErr]     = useState(null)
  const [tab,     setTab]     = useState('score')

  useEffect(() => {
    let cancelled = false
    setDetail(null); setReviews(null); setPage(1); setErr(null); setTab('score')
    api.detail(gmapId)
      .then(d => { if (!cancelled) setDetail(d) })
      .catch(e => { if (!cancelled) setErr(e.message) })
    return () => { cancelled = true }
  }, [gmapId])

  useEffect(() => {
    if (tab !== 'reviews') return
    let cancelled = false
    api.reviews(gmapId, page, 8)
      .then(r => { if (!cancelled) setReviews(r) })
      .catch(() => {})
    return () => { cancelled = true }
  }, [gmapId, page, tab])

  const rootClass = variant === 'panel' ? 'detail-panel' : 'detail-root'

  const hourRows = useMemo(() => parseHours(detail?.hours), [detail?.hours])

  if (err) {
    return (
      <div className={rootClass}>
        <div className="detail-content">
          <button className="btn ghost" onClick={onBack}>{closeLabel}</button>
          <p style={{ color: '#b00020' }}>{err}</p>
        </div>
      </div>
    )
  }
  if (!detail) {
    return (
      <div className={rootClass}>
        <div className="detail-content">Loading…</div>
      </div>
    )
  }

  const aspects = detail.aspects || {}

  // Overall match: percentage. Individual aspects: out of 5 with sentiment glyph.
  const overallPct = lastSearchScore?.final_score != null ? (lastSearchScore.final_score * 100) : null
  const toFive = (v) => (v == null ? null : v * 5)

  // Price uses RAW `aspect_price` (not blended). The 50/50 blend is only used
  // by the overall ranker; surfaced values stay interpretable as pure ABSA.
  const aspectCells = [
    { label: 'Food',      Icon: IconUtensils,                        v: toFive(aspects.food)      },
    { label: 'Service',   MSName: 'concierge',                       v: toFive(aspects.service)   },
    { label: 'Price',     Icon: IconDollar,                          v: toFive(aspects.price)     },
    { label: 'Wait time', Icon: IconClock,                           v: toFive(aspects.wait_time) },
  ]

  return (
    <div className={rootClass}>
      {/* ── Sticky header (name + meta + google link + tabs) ── */}
      <div className="detail-sticky">
        <div className="detail-topbar">
          <button className="btn outline sm" onClick={onBack}>{closeLabel}</button>
        </div>
        <div className="detail-header">
          <h1 className="detail-name">{detail.name}</h1>
          <div className="detail-header-meta">
            {detail.borough && <span className="rating-star">{detail.borough}</span>}
            {detail.address && <><span className="bullet">·</span><span>{detail.address}</span></>}
          </div>
          {(detail.avg_rating != null || detail.price) && (
            <div className="detail-header-meta secondary">
              {detail.avg_rating != null && <span>★ {detail.avg_rating.toFixed(1)}</span>}
              {detail.price && <span className="mono-meta" style={{ fontSize: 13 }}>{detail.price}</span>}
            </div>
          )}
          {detail.url && (
            <div style={{ marginTop: 12 }}>
              <a className="link" href={detail.url} target="_blank" rel="noreferrer">View on Google Maps →</a>
            </div>
          )}
          <div className="loc-mode-tabs detail-tabs" style={{ marginTop: 16 }}>
            <button className={tab === 'score'   ? 'active' : ''} onClick={() => setTab('score')}>Satisfaction Score</button>
            <button className={tab === 'detail'  ? 'active' : ''} onClick={() => setTab('detail')}>Detail</button>
            <button className={tab === 'reviews' ? 'active' : ''} onClick={() => setTab('reviews')}>Reviews</button>
          </div>
        </div>
      </div>

      {/* ── Scrollable tab body ── */}
      <div className="detail-tabbody">
        {tab === 'score' && (
          <>
            {overallPct != null && (
              <div className="scores-grid overall">
                <div className="score-cell overall-cell">
                  <div className="score-cell-head">
                    <IconTarget size={14} />
                    <span className="mono-label">Overall Matching Score</span>
                  </div>
                  <div className="value">{overallPct.toFixed(0)}<span className="out-of">%</span></div>
                  <div className="bar" style={{ width: `${Math.max(0, Math.min(100, overallPct))}%` }} />
                </div>
              </div>
            )}
            <div className="scores-grid aspects">
              {aspectCells.map(({ label, Icon, MSName, v }) => {
                const sentiment = sentimentName(v)
                return (
                  <div key={label} className="score-cell">
                    <div className="score-cell-head">
                      {sentiment && <MS name={sentiment} size={20} className="sentiment-glyph" />}
                      {Icon ? <Icon size={14} /> : <MS name={MSName} size={16} />}
                      <span className="mono-label">{label}</span>
                    </div>
                    <div className="value">
                      {v == null ? '—' : <>{v.toFixed(1)}<span className="out-of">/5</span></>}
                    </div>
                    <div className="bar" style={{ width: `${Math.max(0, Math.min(5, v || 0)) * 20}%` }} />
                  </div>
                )
              })}
            </div>
          </>
        )}

        {tab === 'detail' && (
          <>
            <div className="mono-label section-head">Details from Google Maps</div>

            {detail.state && (
              <section className="section">
                <div className="mono-label section-sub">Status</div>
                <p style={{ fontSize: 14, lineHeight: 1.5, margin: 0, color: 'var(--text)' }}>{detail.state}</p>
              </section>
            )}

            {detail.description && (
              <section className="section">
                <div className="mono-label section-sub">Description</div>
                <p style={{ fontSize: 15, lineHeight: 1.6, margin: 0 }}>{detail.description}</p>
              </section>
            )}

            {detail.category?.length > 0 && (
              <section className="section">
                <div className="mono-label section-sub">Category</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {detail.category.map((c, i) => (
                    <span key={i} className="chip" style={{ background: 'var(--accent-bg)' }}>{c}</span>
                  ))}
                </div>
              </section>
            )}

            <section className="section">
              <div className="mono-label section-sub">Hours</div>
              {hourRows.length === 0 ? (
                <div className="mono-meta">-</div>
              ) : (
                <table className="hours-table">
                  <tbody>
                    {hourRows.map((row) => (
                      <tr key={row.day}>
                        <th>{row.day}</th>
                        <td>
                          {row.closed
                            ? <span className="closed">Closed</span>
                            : row.raw
                              ? row.raw
                              : <>{row.open} – {row.close}</>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>

            <section className="section">
              <div className="mono-label section-sub">Other info</div>
              {!detail.misc || Object.keys(detail.misc).length === 0 ? (
                <div className="mono-meta">-</div>
              ) : (
                <div className="misc-grid">
                  {Object.entries(detail.misc).map(([k, v]) => (
                    <div key={k} className="misc-row">
                      <div className="misc-key">{k}</div>
                      <div className="misc-val">{formatValue(v)}</div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}

        {tab === 'reviews' && (
          <section>
            <div className="mono-label section-head">
              Reviews {reviews && `(${reviews.total.toLocaleString()})`}
            </div>
            {!reviews && <div style={{ color: 'var(--muted)' }}>Loading reviews…</div>}
            {reviews && reviews.reviews.length === 0 && <div style={{ color: 'var(--muted)' }}>No reviews.</div>}
            {reviews && reviews.reviews.length > 0 && (
              <>
                <div className="review-columns">
                  {reviews.reviews.map((r, i) => (
                    <div key={i} className="review-item">
                      {r.text && <div className="review-text">&ldquo;{r.text}&rdquo;</div>}
                      {r.photos?.length > 0 && (
                        <div className="review-photos">
                          {r.photos.map((url, j) => <ReviewPhoto key={j} url={url} />)}
                        </div>
                      )}
                      <div className="review-meta">
                        — {r.reviewer_name || 'Anonymous'}
                        {r.rating != null && ` · ${r.rating.toFixed(1)}★`}
                        {r.time && ` · ${formatTime(r.time)}`}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="pagination">
                  <button className="btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
                  <span className="mono-meta">
                    page {page} / {Math.max(1, Math.ceil(reviews.total / reviews.page_size))}
                  </span>
                  <button
                    className="btn"
                    disabled={page >= Math.ceil(reviews.total / reviews.page_size)}
                    onClick={() => setPage(p => p + 1)}
                  >Next →</button>
                </div>
              </>
            )}
          </section>
        )}
      </div>
    </div>
  )
}

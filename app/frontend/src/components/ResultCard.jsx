import { MS } from './Icons.jsx'
import { sentimentName } from '../lib/sentiment.js'

export default function ResultCard({ r, hovered, selected, onHover, onClick }) {
  const isTop5 = r.rank <= 5
  const scoreFive = r.final_score != null ? r.final_score * 5 : null
  const sentiment = sentimentName(scoreFive)
  const matchPct = r.avg_similarity != null ? Math.round(r.avg_similarity * 100) : null

  return (
    <div
      className={'result-card' + (hovered ? ' hovered' : '') + (selected ? ' selected' : '')}
      onMouseEnter={() => onHover?.(r.gmap_id)}
      onMouseLeave={() => onHover?.(null)}
      onClick={onClick}
    >
      <div className={'result-rank' + (isTop5 ? ' top5' : '')}>
        {String(r.rank).padStart(2, '0')}
      </div>
      <div className="result-main">
        <div className="result-name">{r.name}</div>
        <div className="result-sub">
          {r.borough && <span>{r.borough}</span>}
          {r.avg_rating != null && (
            <>
              <span style={{ opacity: 0.4 }}>·</span>
              <span>★ {r.avg_rating.toFixed(1)}</span>
            </>
          )}
          {r.price && (
            <>
              <span style={{ opacity: 0.4 }}>·</span>
              <span>{r.price}</span>
            </>
          )}
          <span style={{ flex: 1 }} />
          <span className="result-score">
            {sentiment && <MS name={sentiment} size={16} className="sentiment-glyph" />}
            {scoreFive != null && <span>{scoreFive.toFixed(1)}</span>}
            {matchPct != null && (
              <>
                <span style={{ opacity: 0.4 }}>·</span>
                <span>{matchPct}% Match</span>
              </>
            )}
          </span>
        </div>
      </div>
    </div>
  )
}

export default function ResultCard({ r, hovered, selected, onHover, onClick, maxScore }) {
  const isTop5 = r.rank <= 5
  const pct = maxScore > 0 ? Math.min(100, (r.final_score / maxScore) * 100) : 0

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
          <span className="result-score">{(r.final_score * 100).toFixed(0)}%</span>
        </div>
        <span
          className="similarity-bar"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

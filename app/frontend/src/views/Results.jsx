import { useMemo, useState } from 'react'
import MapView       from '../components/MapView.jsx'
import ResultCard    from '../components/ResultCard.jsx'
import Spinner       from '../components/Spinner.jsx'
import Detail        from './Detail.jsx'
import {
  IconUtensils, IconClock, IconDollar, IconUndo, MS,
} from '../components/Icons.jsx'

// 4-aspect satisfaction sort. Overall isn't a button — it's the default
// (preserves the search ranker's order); the user reverts via the Revert
// button when an aspect sort is active. Price uses raw `aspect_price`.
const ASPECT_SORTS = [
  { key: 'food',    Icon: IconUtensils, label: 'Food',    field: 'aspect_food'      },
  { key: 'service', MSName: 'concierge', label: 'Service', field: 'aspect_service'   },
  { key: 'wait',    Icon: IconClock,    label: 'Wait',    field: 'aspect_wait_time' },
  { key: 'price',   Icon: IconDollar,   label: 'Price',   field: 'aspect_price'     },
]

const SORT_LABELS = {
  overall: 'Overall Ranking',
  food:    'Food',
  service: 'Service',
  wait:    'Wait',
  price:   'Price',
}

export default function Results({
  searchState,
  response, loading, error,
  selectedId, onSelectResult,
  lastSearchScore,
}) {
  const [hoveredId, setHoveredId] = useState(null)
  const [sheetExpanded, setSheetExpanded] = useState(true)
  const [sortKey, setSortKey] = useState('overall')

  const rawResults = response?.results || []

  // Sort client-side using the chosen field; null values sink to the bottom.
  const results = useMemo(() => {
    if (sortKey === 'overall') return rawResults
    const s = ASPECT_SORTS.find(x => x.key === sortKey)
    if (!s) return rawResults
    return [...rawResults].sort((a, b) => {
      const va = a[s.field]; const vb = b[s.field]
      const na = va == null, nb = vb == null
      if (na && nb) return 0
      if (na) return 1
      if (nb) return -1
      return vb - va
    })
  }, [rawResults, sortKey])

  const maxScore = rawResults[0]?.final_score ?? 1
  const center = searchState.pin
  const filteredOut = response
    ? Math.max(0, response.total_candidates - response.filtered_candidates)
    : 0

  return (
    <div className="results-root">
      <div className="map-layer">
        <MapView
          mode="results"
          center={center}
          results={rawResults}
          userPin={searchState.uiMode === 'nearby' ? searchState.pin : null}
          hoveredId={hoveredId}
          selectedId={selectedId}
          onMarkerHover={setHoveredId}
          onMarkerClick={onSelectResult}
          fitTrigger={response?.query_effective}
        />
      </div>

      {/* Sidebar: sticky header + scrolling list */}
      <aside className={'sidebar ' + (sheetExpanded ? 'expanded' : 'collapsed')}>
        <div className="sidebar-handle" onClick={() => setSheetExpanded(e => !e)} />

        {response && !loading && (
          <div className="sidebar-sticky-head">
            <div className="results-headline">
              <span className="results-headline-main">
                Top {rawResults.length} Results Sorted by{' '}
                <strong>{SORT_LABELS[sortKey] || 'Overall Ranking'}</strong>.
              </span>
              {filteredOut > 0 && (
                <span
                  className="results-headline-sub"
                  title={`${filteredOut} of the top ${response.total_candidates} semantic candidates were dropped by your filters.`}
                >
                  ({filteredOut} results are filtered out by time, location, and dietary filter.)
                </span>
              )}
            </div>
            <div className="results-meta">
              <span className="mono-meta">
                retrieval {response.retrieval_ms.toFixed(0)}ms · rank {response.rank_ms.toFixed(0)}ms
              </span>
            </div>
            <div className="sort-section">
              <div className="mono-label sort-label">Reorder the result by user's satisfaction on…</div>
              <div className="sort-row">
                {ASPECT_SORTS.map(({ key, Icon, MSName, label }) => (
                  <button
                    key={key}
                    className={'sort-btn' + (sortKey === key ? ' active' : '')}
                    onClick={() => setSortKey(key)}
                    title={label}
                  >
                    {Icon ? <Icon size={13} /> : <MS name={MSName} size={15} />}
                    <span>{label}</span>
                  </button>
                ))}
              </div>
              {sortKey !== 'overall' && (
                <button
                  className="revert-btn"
                  onClick={() => setSortKey('overall')}
                  title="Restore the search engine's overall ranking"
                >
                  <IconUndo size={13} />
                  <span>Revert to overall ranking</span>
                </button>
              )}
            </div>
          </div>
        )}

        <div className="sidebar-body">
          {error && (
            <div style={{ padding: 20, color: '#b00020' }}>
              {error}
            </div>
          )}
          {response && !loading && (
            <div className="result-list">
              {results.map((r) => (
                <ResultCard
                  key={r.gmap_id}
                  r={r}
                  hovered={hoveredId === r.gmap_id}
                  selected={selectedId === r.gmap_id}
                  onHover={setHoveredId}
                  onClick={() => onSelectResult?.(r.gmap_id)}
                  maxScore={maxScore}
                />
              ))}
              {results.length === 0 && (
                <div style={{ padding: 28, textAlign: 'center', color: 'var(--muted)', fontSize: 13 }}>
                  No matches. Try relaxing your filters or searching a different area.
                </div>
              )}
            </div>
          )}
        </div>

        {loading && <Spinner label="Searching" />}
      </aside>

      {/* Inline detail panel on desktop */}
      {selectedId && (
        <Detail
          variant="panel"
          gmapId={selectedId}
          lastSearchScore={lastSearchScore}
          onBack={() => onSelectResult?.(null)}
          closeLabel="✕ Close"
        />
      )}
    </div>
  )
}

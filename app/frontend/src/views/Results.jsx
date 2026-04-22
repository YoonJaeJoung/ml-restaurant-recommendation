import { useMemo, useState } from 'react'
import MapView       from '../components/MapView.jsx'
import ResultCard    from '../components/ResultCard.jsx'
import Spinner       from '../components/Spinner.jsx'
import Detail        from './Detail.jsx'
import {
  IconTarget, IconStar, IconUtensils, IconService, IconClock, IconDollar,
} from '../components/Icons.jsx'

// Sort keys + the field each reads. Overall preserves the original rank.
// Laid out as two fixed rows: [Overall, Google] on row 1 and the four aspects
// on row 2 so the visual hierarchy matches the score cells in the Detail panel.
const SORT_ROW_1 = [
  { key: 'overall', Icon: IconTarget,   label: 'Overall', field: 'final_score'          },
  { key: 'rating',  Icon: IconStar,     label: 'Google',  field: 'avg_rating'           },
]
const SORT_ROW_2 = [
  { key: 'food',    Icon: IconUtensils, label: 'Food',    field: 'aspect_food'          },
  { key: 'service', Icon: IconService,  label: 'Service', field: 'aspect_service'       },
  { key: 'wait',    Icon: IconClock,    label: 'Wait',    field: 'aspect_wait_time'     },
  { key: 'price',   Icon: IconDollar,   label: 'Price',   field: 'aspect_price_blended' },
]
const SORTS = [...SORT_ROW_1, ...SORT_ROW_2]

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
    const s = SORTS.find(x => x.key === sortKey)
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

      {/* Sidebar: sticky header (meta + sort row), scrolling list */}
      <aside className={'sidebar ' + (sheetExpanded ? 'expanded' : 'collapsed')}>
        <div className="sidebar-handle" onClick={() => setSheetExpanded(e => !e)} />

        {response && !loading && (
          <div className="sidebar-sticky-head">
            <div className="results-meta">
              <span className="mono-label">
                {rawResults.length} places
                {response.filtered_candidates < response.total_candidates && (
                  <span
                    className="filtered-count"
                    title={`Your location / time filters removed ${response.total_candidates - response.filtered_candidates} of the ${response.total_candidates} semantic candidates`}
                  >
                    {' · '}{response.total_candidates - response.filtered_candidates} filtered out
                  </span>
                )}
              </span>
              <span className="mono-meta">
                retrieval {response.retrieval_ms.toFixed(0)}ms · rank {response.rank_ms.toFixed(0)}ms
              </span>
            </div>
            <div className="sort-section">
              <div className="mono-label sort-label">Sort by…</div>
              {[SORT_ROW_1, SORT_ROW_2].map((row, i) => (
                <div key={i} className="sort-row">
                  {row.map(({ key, Icon, label }) => (
                    <button
                      key={key}
                      className={'sort-btn' + (sortKey === key ? ' active' : '')}
                      onClick={() => setSortKey(key)}
                      title={label}
                    >
                      <Icon size={13} />
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              ))}
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

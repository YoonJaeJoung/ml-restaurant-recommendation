import { useMemo, useState } from 'react'
import FilterPanel      from '../components/FilterPanel.jsx'
import InspireBuilder   from '../components/InspireBuilder.jsx'
import { SpinnerInline } from '../components/Spinner.jsx'
import { IconSearch, IconChevronDown, IconChevronUp } from '../components/Icons.jsx'

function formatDayTimeSummary(visit, anyTime) {
  if (anyTime) return 'Any time'
  if (!visit) return 'Today · now'
  const today = new Date()
  const tomorrow = new Date(); tomorrow.setDate(today.getDate() + 1)
  const sameDay = (a, b) =>
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
  let dayLabel
  if (sameDay(visit, today)) dayLabel = 'Today'
  else if (sameDay(visit, tomorrow)) dayLabel = 'Tomorrow'
  else dayLabel = visit.toLocaleDateString('en-US', { weekday: 'short' })
  const hh = String(visit.getHours()).padStart(2, '0')
  const mm = String(visit.getMinutes()).padStart(2, '0')
  return `${dayLabel} · ${hh}:${mm}`
}
function formatLocationSummary({ uiMode, radiusKm, boroughs, bbox, polygon }) {
  if (uiMode === 'nearby') {
    const r = radiusKm < 1 ? `${Math.round(radiusKm * 1000)} m` : `${radiusKm.toFixed(1)} km`
    return `Nearby ${r}`
  }
  if (uiMode === 'borough') {
    if (!boroughs || boroughs.length === 0) return 'All NYC'
    if (boroughs.length === 5) return 'All NYC'
    if (boroughs.length === 1) return boroughs[0]
    return `${boroughs.length} boroughs`
  }
  if (uiMode === 'area') {
    if (polygon) return `Polygon (${polygon.length} pts)`
    if (bbox)    return 'Map viewport'
    return 'Pick an area'
  }
  return '—'
}

export default function Home({ searchState, setSearchState, onSearch, onBrowseAll, onResetDefaults, loading }) {
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [inspireOpen, setInspireOpen] = useState(false)
  const [preInspireQuery, setPreInspireQuery] = useState('')
  const [queryFocused, setQueryFocused] = useState(false)

  const dayTimeSummary  = useMemo(() =>
    formatDayTimeSummary(searchState.visitDate, searchState.anyTime),
    [searchState.visitDate, searchState.anyTime])
  const locationSummary = useMemo(() =>
    formatLocationSummary(searchState),
    [searchState])

  const startInspire = () => {
    setPreInspireQuery(searchState.query || '')
    setInspireOpen(true)
  }
  const cancelInspire = () => {
    setInspireOpen(false)
    setSearchState(s => ({ ...s, query: preInspireQuery, toggles: { occasion: null, vibe: null, cuisine: null, priority: null } }))
  }
  const inspireSearch = (toggles) => {
    setInspireOpen(false)
    setSearchState(s => ({ ...s, toggles }))
    requestAnimationFrame(() => onSearch())
  }
  const inspireUpdate = (query, toggles) => {
    setSearchState(s => ({ ...s, query, toggles }))
  }

  const handleClear = () => { onResetDefaults?.(); setFiltersOpen(false) }
  const handleSave  = () => { setFiltersOpen(false) }

  return (
    <div className="home-wrap">
      <div className="home-title-block">
        <h1 className="home-title">Find Your Next Favorite Restaurant in NYC</h1>
        <p className="home-subtitle">
          Tell us what you want. We&apos;ll search 2.1M reviews across 19,500 NYC restaurants,
          weigh what you care about, and rank the best matches.
        </p>
      </div>

      {/* ─── Filter accordion ─── */}
      <div className="filter-accordion">
        <div
          className={'filter-head' + (filtersOpen ? ' open' : '')}
          onClick={() => setFiltersOpen(o => !o)}
          role="button"
        >
          <span className="chevron">
            {filtersOpen ? <IconChevronUp size={12} /> : <IconChevronDown size={12} />}
          </span>
          <span className="mono-label">Filters</span>
          <span className="filter-summary">
            <span className="pill">{dayTimeSummary}</span>
            <span className="pill">{locationSummary}</span>
          </span>
          {!filtersOpen && <span className="mono-meta">edit</span>}
        </div>
        {filtersOpen && (
          <div className="filter-body">
            <FilterPanel searchState={searchState} setSearchState={setSearchState} />
            <div className="filter-footer">
              <button className="btn ghost"   onClick={handleClear}>Clear</button>
              <button className="btn primary" onClick={handleSave}>Save</button>
            </div>
          </div>
        )}
      </div>

      {/* ─── Query box with Need-inspiration? ─── */}
      <div className={'home-query' + (queryFocused || inspireOpen ? ' focused' : '')}>
        <div className="home-query-row">
          <IconSearch size={16} className="home-query-icon" />
          <input
            type="text"
            className="home-query-input"
            value={searchState.query || ''}
            onChange={(e) => setSearchState(s => ({ ...s, query: e.target.value }))}
            onKeyDown={(e) => { if (e.key === 'Enter' && !inspireOpen) onSearch() }}
            onFocus={() => setQueryFocused(true)}
            onBlur={() => setQueryFocused(false)}
            placeholder={inspireOpen ? 'Picks are filling this in…' : 'e.g. "cozy italian date night outdoor"'}
            autoFocus
          />
          {!inspireOpen && (
            <button className="inspire-btn" onClick={startInspire}>
              ✨ Need inspiration?
            </button>
          )}
        </div>
        {inspireOpen && (
          <InspireBuilder
            initialQuery={searchState.query}
            initialToggles={searchState.toggles}
            onChange={inspireUpdate}
            onCancel={cancelInspire}
            onSearch={inspireSearch}
          />
        )}
      </div>

      {/* ─── Primary CTA row: Browse (outlined, left) + spacer + Search (right) ─── */}
      {!inspireOpen && (
        <div className="home-cta-row">
          <button className="btn primary outline cta" onClick={onBrowseAll}>
            Browse all restaurants
          </button>
          <span className="spacer" />
          <button className="btn primary cta" onClick={onSearch} disabled={loading}>
            {loading ? <><SpinnerInline />Searching…</> : 'Search'}
          </button>
        </div>
      )}
    </div>
  )
}

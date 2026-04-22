import { useCallback, useMemo, useState } from 'react'
import Home         from './views/Home.jsx'
import Results      from './views/Results.jsx'
import BrowseAll    from './views/BrowseAll.jsx'
import HelpModal    from './components/HelpModal.jsx'
import AboutModal   from './components/AboutModal.jsx'
import FilterPanel  from './components/FilterPanel.jsx'
import { SpinnerInline } from './components/Spinner.jsx'
import {
  IconArrowLeft, IconChevronDown, IconChevronUp,
} from './components/Icons.jsx'
import { api }      from './api/client.js'

const DEFAULT_SEARCH_STATE = {
  query: '',
  toggles: { occasion: null, vibe: null, cuisine: null, priority: null },

  visitDate: new Date(),
  anyTime: false,

  uiMode: 'borough',         // default: All NYC via Select Borough tab
  boroughs: null,            // null = All NYC
  radiusKm: 1.0,
  pin: null,

  bbox: null,
  polygon: null,
}

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

export default function App() {
  const [view, setView] = useState('home')
  const [searchState, setSearchState] = useState(DEFAULT_SEARCH_STATE)
  const [response, setResponse] = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)
  const [helpOpen, setHelpOpen] = useState(false)
  const [aboutOpen, setAboutOpen] = useState(false)
  const [toolbarOpen, setToolbarOpen] = useState(false)
  const [detailId, setDetailId] = useState(null)       // inline right-side panel on Results
  const [browseDetailId, setBrowseDetailId] = useState(null)  // inline right-side panel on Browse

  const buildLocationPayload = (s) => {
    if (s.uiMode === 'nearby') {
      return {
        mode: 'radius',
        center: s.pin ? [s.pin.lat, s.pin.lon] : null,
        radius_km: s.radiusKm,
      }
    }
    if (s.uiMode === 'borough') {
      if (!s.boroughs || s.boroughs.length === 0 || s.boroughs.length === 5) {
        return { mode: 'all' }
      }
      return { mode: 'borough', boroughs: s.boroughs }
    }
    if (s.uiMode === 'area') {
      if (s.polygon && s.polygon.length >= 3) return { mode: 'polygon', polygon: s.polygon }
      if (s.bbox)                              return { mode: 'bbox', bbox: s.bbox }
      return { mode: 'all' }
    }
    return { mode: 'all' }
  }

  const buildPayload = useCallback(() => {
    const s = searchState
    const timeObj = { any_time: s.anyTime }
    if (!s.anyTime && s.visitDate) {
      timeObj.at = s.visitDate.toISOString().replace('Z', '')
    }
    return {
      query: s.query,
      toggles: s.toggles,
      location: buildLocationPayload(s),
      time: timeObj,
      limit: 30,
    }
  }, [searchState])

  const runSearch = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const payload = buildPayload()
      const hasQuery = !!payload.query?.trim()
      const hasToggles = Object.values(payload.toggles || {}).some(
        v => v && v !== 'No preference' && v !== 'None'
      )
      if (!hasQuery && !hasToggles) {
        setError('Enter a query or pick at least one option.')
        setLoading(false)
        return
      }
      if (payload.location.mode === 'radius' && !payload.location.center) {
        setError('No pin set — open Search nearby and click “Current Location”, or click the map to place a pin.')
        setLoading(false)
        return
      }
      setView('results')
      setDetailId(null)
      setToolbarOpen(false)
      const resp = await api.search(payload)
      setResponse(resp)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [buildPayload])

  const resetDefaults = useCallback(() => {
    setSearchState(s => ({
      ...DEFAULT_SEARCH_STATE,
      visitDate: new Date(),
      query: s.query,
      toggles: s.toggles,
    }))
  }, [])

  const goHome = useCallback(() => {
    setView('home'); setDetailId(null); setBrowseDetailId(null); setToolbarOpen(false)
  }, [])

  const lastSearchScore = detailId && response
    ? {
        query: response.query_effective,
        final_score: response.results.find(r => r.gmap_id === detailId)?.final_score,
      }
    : null

  // ── Topbar slots ──────────────────────────────────────────────────
  const dayTimeSummary  = useMemo(() =>
    formatDayTimeSummary(searchState.visitDate, searchState.anyTime),
    [searchState.visitDate, searchState.anyTime])
  const locationSummary = useMemo(() =>
    formatLocationSummary(searchState),
    [searchState])
  const queryLabel = searchState.query?.trim() || response?.query_effective || '(empty query)'

  const topbarLeft = view === 'home' ? (
    <button
      className="brand-pill"
      onClick={() => setAboutOpen(true)}
      title="About Noble Jaguars"
    >Noble Jaguars</button>
  ) : (
    <button
      className="icon-btn"
      onClick={goHome}
      aria-label="Back to home"
      title="Home"
    ><IconArrowLeft size={15} /> Home</button>
  )

  const topbarCenter = view === 'results' ? (
    <button
      className={'query-pill' + (toolbarOpen ? ' open' : '')}
      onClick={() => setToolbarOpen(o => !o)}
      title="Click to edit query & filters"
    >
      <span className="query-pill-query">&ldquo;{queryLabel}&rdquo;</span>
      <span className="query-pill-filters">
        <span className="query-pill-dot">·</span>
        <span>{dayTimeSummary}</span>
        <span className="query-pill-dot">·</span>
        <span>{locationSummary}</span>
      </span>
      <span className="query-pill-edit">
        {toolbarOpen ? <IconChevronUp size={12} /> : <IconChevronDown size={12} />}
      </span>
    </button>
  ) : null

  const topbarRight = (
    <button
      className="icon-btn round help-btn"
      aria-label="How does this work?"
      onClick={() => setHelpOpen(true)}
      title="How does this work?"
    >?</button>
  )

  // ── Topbar drop-down (Results only) ───────────────────────────────
  const topbarDropdown = view === 'results' && toolbarOpen ? (
    <div className="topbar-dropdown">
      <div className="topbar-dropdown-body">
        <div className="filter-section">
          <div className="mono-label sublabel">Query</div>
          <input
            type="text"
            className="input"
            value={searchState.query || ''}
            onChange={(e) => setSearchState(s => ({ ...s, query: e.target.value }))}
            onKeyDown={(e) => { if (e.key === 'Enter') runSearch() }}
            placeholder="Refine your search…"
            autoFocus
          />
        </div>
        <FilterPanel searchState={searchState} setSearchState={setSearchState} />
        <div className="filter-footer">
          <button className="btn ghost"   onClick={() => { resetDefaults(); setToolbarOpen(false) }}>Clear</button>
          <button className="btn"         onClick={() => setToolbarOpen(false)}>Save</button>
          <button className="btn primary" onClick={runSearch} disabled={loading}>
            {loading ? <><SpinnerInline />Searching…</> : 'Search'}
          </button>
        </div>
      </div>
    </div>
  ) : null

  return (
    <div className="app-root">
      <div className={'topbar' + (view === 'home' ? ' on-home' : '')}>
        <div className="topbar-left">{topbarLeft}</div>
        <div className="topbar-center">{topbarCenter}</div>
        <div className="topbar-right">{topbarRight}</div>
      </div>
      {topbarDropdown}

      {view === 'home' && (
        <Home
          searchState={searchState}
          setSearchState={setSearchState}
          onSearch={runSearch}
          onBrowseAll={() => setView('browse')}
          onResetDefaults={resetDefaults}
          loading={loading}
          FilterPanelComponent={FilterPanel}
        />
      )}

      {view === 'results' && (
        <Results
          searchState={searchState}
          response={response}
          loading={loading}
          error={error}
          selectedId={detailId}
          onSelectResult={setDetailId}
          lastSearchScore={lastSearchScore}
        />
      )}

      {view === 'browse' && (
        <BrowseAll
          selectedId={browseDetailId}
          onSelectResult={setBrowseDetailId}
        />
      )}

      <HelpModal  open={helpOpen}  onClose={() => setHelpOpen(false)} />
      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />
    </div>
  )
}

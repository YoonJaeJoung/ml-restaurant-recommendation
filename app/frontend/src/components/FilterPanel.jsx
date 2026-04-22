import DayTimePicker    from './DayTimePicker.jsx'
import LocationControls from './LocationControls.jsx'

// Shared filter body reused by Home's accordion AND the Results topbar drop-down.
// All state lives in `searchState` upstream; this component is just wiring.
export default function FilterPanel({ searchState, setSearchState }) {
  return (
    <>
      <div className="filter-section">
        <DayTimePicker
          value={searchState.visitDate}
          onChange={(d) => setSearchState(s => ({ ...s, visitDate: d }))}
          anyTime={searchState.anyTime}
          onAnyTime={(v) => setSearchState(s => ({ ...s, anyTime: v }))}
        />
      </div>
      <div className="filter-section">
        <LocationControls
          uiMode={searchState.uiMode}
          onUiMode={(m) => setSearchState(s => ({ ...s, uiMode: m }))}
          boroughs={searchState.boroughs}
          onBoroughs={(v) => setSearchState(s => ({ ...s, boroughs: v }))}
          radiusKm={searchState.radiusKm}
          onRadiusKm={(v) => setSearchState(s => ({ ...s, radiusKm: v }))}
          pin={searchState.pin}
          setPin={(p) => setSearchState(s => ({ ...s, pin: p }))}
          bbox={searchState.bbox}
          setBbox={(b) => setSearchState(s => ({ ...s, bbox: b }))}
          polygon={searchState.polygon}
          setPolygon={(p) => setSearchState(s => ({ ...s, polygon: p }))}
        />
      </div>
    </>
  )
}

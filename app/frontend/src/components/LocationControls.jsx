import BoroughSelector from './BoroughSelector.jsx'
import MapInline       from './MapInline.jsx'

// Tab order: Select Borough → Search nearby → Select area from map.
const MODES = [
  { key: 'borough', label: 'Select Borough'        },
  { key: 'nearby',  label: 'Search nearby'         },
  { key: 'area',    label: 'Select area from map'  },
]

// Geolocation no longer fires when the "Search nearby" tab opens — it only
// fires when the user clicks the "Current Location" button inside the inline
// map (MapInline).
export default function LocationControls({
  uiMode, onUiMode,
  boroughs, onBoroughs,
  radiusKm, onRadiusKm,
  pin, setPin,
  bbox, polygon,
  setBbox, setPolygon,
}) {
  return (
    <div>
      <div className="mono-label sublabel">Where are you looking?</div>
      <div className="loc-mode-tabs">
        {MODES.map((m) => (
          <button
            key={m.key}
            className={uiMode === m.key ? 'active' : ''}
            onClick={() => onUiMode(m.key)}
          >{m.label}</button>
        ))}
      </div>

      {uiMode === 'borough' && (
        <BoroughSelector selected={boroughs} onChange={onBoroughs} />
      )}

      {uiMode === 'nearby' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: 'var(--muted)', flexWrap: 'wrap', marginBottom: 12 }}>
            <span>Radius:</span>
            <input
              type="range"
              min={0.1} max={2.5} step={0.1}
              value={radiusKm}
              onChange={(e) => onRadiusKm(parseFloat(e.target.value))}
              style={{ accentColor: 'var(--accent)', flex: 1, minWidth: 160, maxWidth: 240 }}
            />
            <span className="mono-meta">
              {radiusKm < 1 ? `${Math.round(radiusKm * 1000)} m` : `${radiusKm.toFixed(1)} km`}
            </span>
            <span className="mono-meta" style={{ marginLeft: 'auto' }}>
              {pin ? `📍 ${pin.lat.toFixed(4)}, ${pin.lon.toFixed(4)}` : 'No pin — click "Current Location" on the map.'}
            </span>
          </div>
          <MapInline
            mode="nearby"
            pin={pin}
            onPinPlace={setPin}
            radiusKm={radiusKm}
          />
        </div>
      )}

      {uiMode === 'area' && (
        <div>
          <p className="mono-meta" style={{ marginBottom: 10 }}>
            {polygon ? `Shape set (${polygon.length} vertices)`
              : bbox ? 'Viewport captured — hit Search to use it.'
              : 'Capture a viewport, or draw a polygon/rectangle.'}
          </p>
          <MapInline
            mode="area"
            pin={pin}
            polygon={polygon}
            onPolygon={setPolygon}
            onCommitBbox={setBbox}
          />
        </div>
      )}
    </div>
  )
}

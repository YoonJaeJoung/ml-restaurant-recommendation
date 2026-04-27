import { useCallback, useRef, useState } from 'react'
import MapView from './MapView.jsx'
import {
  IconLocate, IconViewport, IconPolygon, IconRectangle,
  IconPlus, IconMinus, IconClose,
} from './Icons.jsx'
import { NYC_FALLBACK } from '../hooks/useGeolocation.js'

/**
 * `mode` is:
 *   'nearby' — show pin + radius circle. "Current Location" button is the ONLY
 *              code path that prompts the browser geolocation permission.
 *   'area'   — three overlay buttons (viewport / polygon / rectangle). When a
 *              shape exists, all three disappear and a single "Clear Selection"
 *              button takes their place.
 */
export default function MapInline({
  mode,
  pin, onPinPlace, radiusKm,
  polygon, onPolygon,
  onCommitBbox,
}) {
  const mapRef = useRef(null)
  const [drawTrigger, setDrawTrigger] = useState(null)
  const [locating, setLocating] = useState(false)

  const captureViewport = useCallback(() => {
    if (!mapRef.current) return
    const b = mapRef.current.getBounds()
    const bbox = [
      [b.getSouth(), b.getWest()],
      [b.getNorth(), b.getEast()],
    ]
    onPolygon?.(null)
    onCommitBbox?.(bbox)
  }, [onCommitBbox, onPolygon])

  const startPolygon   = () => setDrawTrigger({ kind: 'startPolygon',   seq: Date.now() })
  const startRectangle = () => setDrawTrigger({ kind: 'startRectangle', seq: Date.now() })
  const clearSelection = () => {
    onPolygon?.(null)
    setDrawTrigger({ kind: 'clear', seq: Date.now() })
  }

  // "Current Location" gates geolocation: only fires here, never on tab open.
  const requestCurrentLocation = useCallback(() => {
    if (locating) return
    setLocating(true)
    if (!('geolocation' in navigator)) {
      onPinPlace?.({ ...NYC_FALLBACK })
      if (mapRef.current) mapRef.current.setView([NYC_FALLBACK.lat, NYC_FALLBACK.lon], 14)
      setLocating(false)
      return
    }
    navigator.geolocation.getCurrentPosition(
      (p) => {
        const loc = { lat: p.coords.latitude, lon: p.coords.longitude }
        onPinPlace?.(loc)
        if (mapRef.current) mapRef.current.setView([loc.lat, loc.lon], 15)
        setLocating(false)
      },
      () => {
        onPinPlace?.({ ...NYC_FALLBACK })
        if (mapRef.current) mapRef.current.setView([NYC_FALLBACK.lat, NYC_FALLBACK.lon], 14)
        setLocating(false)
      },
      { timeout: 6000, enableHighAccuracy: false },
    )
  }, [locating, onPinPlace])

  // Custom zoom control (replaces leaflet's default).
  const zoomIn  = () => mapRef.current && mapRef.current.zoomIn()
  const zoomOut = () => mapRef.current && mapRef.current.zoomOut()

  const initial = pin ? { lat: pin.lat, lon: pin.lon } : undefined
  const hasShape = Array.isArray(polygon) && polygon.length >= 3

  return (
    <div className="map-inline">
      {/* Top-left overlay buttons */}
      {mode === 'nearby' && (
        <div className="map-inline-overlay">
          <button className="btn primary sm" onClick={requestCurrentLocation} disabled={locating}>
            <IconLocate size={14} />
            {locating ? 'Locating…' : 'Current Location'}
          </button>
        </div>
      )}
      {mode === 'area' && !hasShape && (
        <div className="map-inline-overlay">
          <button className="btn primary sm" onClick={captureViewport}>
            <IconViewport size={14} /> Use current viewport
          </button>
          <button className="btn primary sm outline" onClick={startPolygon}>
            <IconPolygon size={14} /> Draw Polygon
          </button>
          <button className="btn primary sm outline" onClick={startRectangle}>
            <IconRectangle size={14} /> Draw Rectangle
          </button>
          <button className="btn primary sm outline" onClick={requestCurrentLocation} disabled={locating}>
            <IconLocate size={14} />
            {locating ? 'Locating…' : 'Current Location'}
          </button>
        </div>
      )}
      {mode === 'area' && hasShape && (
        <div className="map-inline-overlay">
          <button className="btn primary sm" onClick={clearSelection}>
            <IconClose size={14} /> Clear Selection
          </button>
          <button className="btn primary sm outline" onClick={requestCurrentLocation} disabled={locating}>
            <IconLocate size={14} />
            {locating ? 'Locating…' : 'Current Location'}
          </button>
        </div>
      )}

      <MapView
        mode={mode === 'nearby' ? 'edit-nearby' : 'edit-area'}
        userPin={pin}
        radiusKm={radiusKm}
        onPinPlace={onPinPlace}
        onPolygon={onPolygon}
        drawTrigger={drawTrigger}
        mapRef={mapRef}
        initialCenter={initial}
        zoom={mode === 'nearby' ? 14 : 12}
      />

      {/* Bottom-left stack: custom zoom pill + hint */}
      <div className="map-inline-zoom">
        <button className="zoom-btn" onClick={zoomIn}  aria-label="Zoom in"><IconPlus  size={14} /></button>
        <button className="zoom-btn" onClick={zoomOut} aria-label="Zoom out"><IconMinus size={14} /></button>
      </div>

      <div className="map-inline-hint">
        {mode === 'nearby'
          ? 'Click anywhere on the map to move your pin.'
          : 'Capture the viewport, or draw a polygon / rectangle.'}
      </div>
    </div>
  )
}

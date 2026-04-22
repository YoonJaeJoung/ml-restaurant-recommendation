import { useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Circle, FeatureGroup, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet.markercluster'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'

const NYC_CENTER = [40.7128, -74.0060]
const NYC_ZOOM   = 11

// Mapbox tile URL template (Streets v12). Read token from Vite env.
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN
const MAPBOX_STYLE = 'mapbox/streets-v12'
const TILE_URL = MAPBOX_TOKEN
  ? `https://api.mapbox.com/styles/v1/${MAPBOX_STYLE}/tiles/{z}/{x}/{y}@2x?access_token=${MAPBOX_TOKEN}`
  : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
const TILE_ATTR = MAPBOX_TOKEN
  ? '&copy; <a href="https://www.mapbox.com/about/maps/">Mapbox</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'

// ── Custom DivIcons ──────────────────────────────────────────────────────────
// Teardrop pins: rotated square with rounded corners except bottom-left, so
// the "tail" points down-left; the content is counter-rotated to stay upright.
const iconFor = (rank, hovered, selected) => {
  const mods = (hovered ? ' hovered' : '') + (selected ? ' selected' : '')
  if (rank && rank <= 5) {
    return L.divIcon({
      className: '',
      html: `<div class="map-teardrop${mods}"><span class="map-teardrop-num">${rank}</span></div>`,
      iconSize: [26, 34],
      iconAnchor: [13, 34],   // point of the teardrop
    })
  }
  return L.divIcon({
    className: '',
    html: `<div class="map-teardrop small${mods}"></div>`,
    iconSize: [14, 18],
    iconAnchor: [7, 18],
  })
}

const userIcon = L.divIcon({
  className: '',
  html: '<div class="pin-user"></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
})

const browseIcon = L.divIcon({
  className: '',
  html: '<div class="map-teardrop small"></div>',
  iconSize: [14, 18],
  iconAnchor: [7, 18],
})


function BboxWatcher({ onBbox }) {
  useMapEvents({
    moveend(e) {
      const b = e.target.getBounds()
      onBbox?.([
        [b.getSouth(), b.getWest()],
        [b.getNorth(), b.getEast()],
      ])
    },
  })
  return null
}

// Click or long-press (touch) drops/moves the radius pin.
function PinDropper({ enabled, onPlace }) {
  useMapEvents({
    click(e) {
      if (!enabled) return
      onPlace?.({ lat: e.latlng.lat, lon: e.latlng.lng })
    },
  })
  return null
}

// DrawControl with polygon + rectangle tools. Rectangles come back as 4-vertex
// polygons (getLatLngs returns a single ring of 4 points) so the upstream
// polygon-filter code handles both shapes identically.
function DrawControl({ onCreated, onDeleted, featureGroup, triggerSignal }) {
  const map = useMap()
  const handlerRef = useRef(null)

  useEffect(() => {
    if (!featureGroup.current) return
    const shape = { color: '#E03E3E', weight: 2, fillOpacity: 0.10 }
    // showArea: false works around a known leaflet-draw 1.0.4 bug where the
    // internal `_getMeasurementString` references an undefined `type` on
    // newer Leaflet (ReferenceError: Can't find variable: type).
    const drawControl = new L.Control.Draw({
      position: 'topright',
      draw: {
        polygon:   { allowIntersection: false, showArea: false, shapeOptions: shape },
        rectangle: { showArea: false, shapeOptions: shape },
        polyline: false, circle: false, marker: false, circlemarker: false,
      },
      edit: { featureGroup: featureGroup.current, remove: true },
    })
    map.addControl(drawControl)
    const createdHandler = (e) => {
      featureGroup.current.clearLayers()
      featureGroup.current.addLayer(e.layer)
      // For both polygon and rectangle: getLatLngs()[0] is the outer ring.
      const raw = e.layer.getLatLngs()
      const ring = Array.isArray(raw[0]) ? raw[0] : raw
      const ll = ring.map(p => [p.lat, p.lng])
      onCreated?.(ll)
    }
    const deletedHandler = () => onDeleted?.()
    map.on(L.Draw.Event.CREATED, createdHandler)
    map.on(L.Draw.Event.DELETED, deletedHandler)
    // expose a handle so the parent can invoke the polygon draw handler programmatically
    handlerRef.current = {
      startPolygon:   () => new L.Draw.Polygon  (map, drawControl.options.draw.polygon  ).enable(),
      startRectangle: () => new L.Draw.Rectangle(map, drawControl.options.draw.rectangle).enable(),
      clearAll:       () => featureGroup.current.clearLayers(),
    }
    return () => {
      map.off(L.Draw.Event.CREATED, createdHandler)
      map.off(L.Draw.Event.DELETED, deletedHandler)
      map.removeControl(drawControl)
      handlerRef.current = null
    }
  }, [map, featureGroup, onCreated, onDeleted])

  // When `triggerSignal` changes, interpret it.
  useEffect(() => {
    if (!triggerSignal || !handlerRef.current) return
    if (triggerSignal.kind === 'startPolygon')   handlerRef.current.startPolygon()
    if (triggerSignal.kind === 'startRectangle') handlerRef.current.startRectangle()
    if (triggerSignal.kind === 'clear') {
      handlerRef.current.clearAll()
      onDeleted?.()
    }
  }, [triggerSignal, onDeleted])

  return null
}

function ViewController({ center, zoom }) {
  const map = useMap()
  useEffect(() => {
    if (!center) return
    map.setView([center.lat, center.lon], zoom ?? map.getZoom(), { animate: true })
  }, [center, zoom, map])
  return null
}

function FitBoundsOnResults({ points, trigger }) {
  const map = useMap()
  useEffect(() => {
    if (!points || points.length === 0) return
    const valid = points.filter(p => p[0] != null && p[1] != null)
    if (valid.length === 0) return
    const bounds = L.latLngBounds(valid.map(p => [p[0], p[1]]))
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trigger])
  return null
}

// Imperative marker cluster layer for the browse-all view. Uses leaflet.markercluster
// directly since react-leaflet doesn't wrap it.
function BrowseClusterLayer({ points, onClick }) {
  const map = useMap()
  const layerRef = useRef(null)
  useEffect(() => {
    if (!points) return
    const cluster = L.markerClusterGroup({
      chunkedLoading: true,
      showCoverageOnHover: false,
      spiderfyOnMaxZoom: true,
      disableClusteringAtZoom: 17,
      iconCreateFunction: (c) => {
        const count = c.getChildCount()
        const size = count > 200 ? ' huge' : count > 50 ? ' large' : ''
        return L.divIcon({
          html: `<div>${count.toLocaleString()}</div>`,
          className: 'marker-cluster' + size,
          iconSize: L.point(40, 40),
        })
      },
    })
    for (const p of points) {
      if (p.latitude == null || p.longitude == null) continue
      const m = L.marker([p.latitude, p.longitude], { icon: browseIcon })
      const ratingStr = p.avg_rating != null ? `★ ${p.avg_rating.toFixed(1)}` : ''
      const priceStr  = p.price ? ` · ${p.price}` : ''
      m.bindTooltip(
        `<strong>${p.name}</strong><br/><span style="font-size:11px;opacity:.7">${ratingStr}${priceStr}${p.borough ? ' · ' + p.borough : ''}</span>`,
        { direction: 'top', offset: L.point(0, -6), opacity: 0.95 }
      )
      m.on('click', () => onClick?.(p.gmap_id))
      cluster.addLayer(m)
    }
    map.addLayer(cluster)
    layerRef.current = cluster
    return () => { if (layerRef.current) map.removeLayer(layerRef.current) }
  }, [map, points, onClick])
  return null
}

// Exposes the current bounds via an imperative ref (for "Search this area" button).
function MapRefExposer({ captureRef }) {
  const map = useMap()
  useEffect(() => {
    if (captureRef) captureRef.current = map
    return () => { if (captureRef) captureRef.current = null }
  }, [captureRef, map])
  return null
}


export default function MapView({
  center,
  zoom = NYC_ZOOM,
  results = [],
  userPin,
  hoveredId,
  selectedId,
  onMarkerHover,
  onMarkerClick,
  mode = 'results',            // 'results' | 'edit-nearby' | 'edit-area' | 'browse'
  radiusKm,
  onPinPlace,
  onBbox,
  onPolygon,
  fitTrigger,
  browsePoints = null,
  onBrowseClick,
  mapRef,                       // imperative: { current: map instance }
  initialCenter: initialCenterProp,
  drawTrigger,                  // { kind: 'startPolygon' | 'clear', seq: number }
}) {
  const featureGroupRef = useRef(null)
  const [initialCenter] = useState(
    initialCenterProp
      ? [initialCenterProp.lat, initialCenterProp.lon]
      : (center ? [center.lat, center.lon] : NYC_CENTER)
  )

  const resultPoints = useMemo(
    () => results.filter(r => r.latitude != null && r.longitude != null),
    [results],
  )

  return (
    <MapContainer
      center={initialCenter}
      zoom={zoom}
      scrollWheelZoom
      zoomControl={false}
      style={{ width: '100%', height: '100%' }}
    >
      <TileLayer
        attribution={TILE_ATTR}
        url={TILE_URL}
        tileSize={MAPBOX_TOKEN ? 512 : 256}
        zoomOffset={MAPBOX_TOKEN ? -1 : 0}
      />

      <MapRefExposer captureRef={mapRef} />
      <BboxWatcher onBbox={onBbox} />
      <PinDropper enabled={mode === 'edit-nearby'} onPlace={onPinPlace} />
      {center && <ViewController center={center} zoom={zoom} />}
      {mode === 'results' && (
        <FitBoundsOnResults
          points={resultPoints.map(r => [r.latitude, r.longitude])}
          trigger={fitTrigger}
        />
      )}

      <FeatureGroup ref={featureGroupRef}>
        {mode === 'edit-area' && (
          <DrawControl
            featureGroup={featureGroupRef}
            onCreated={onPolygon}
            onDeleted={() => onPolygon?.(null)}
            triggerSignal={drawTrigger}
          />
        )}
      </FeatureGroup>

      {/* User/radius center pin */}
      {userPin && (mode === 'edit-nearby' || mode === 'results') && (
        <>
          <Marker position={[userPin.lat, userPin.lon]} icon={userIcon} />
          {(mode === 'edit-nearby') && radiusKm && (
            <Circle
              center={[userPin.lat, userPin.lon]}
              radius={radiusKm * 1000}
              pathOptions={{ color: '#1E3A8A', weight: 1, fillOpacity: 0.06 }}
            />
          )}
        </>
      )}

      {/* Browse-all: marker cluster layer */}
      {mode === 'browse' && browsePoints && (
        <BrowseClusterLayer points={browsePoints} onClick={onBrowseClick} />
      )}

      {/* Result markers */}
      {mode === 'results' && resultPoints.map((r) => (
        <Marker
          key={r.gmap_id}
          position={[r.latitude, r.longitude]}
          icon={iconFor(r.rank, hoveredId === r.gmap_id, selectedId === r.gmap_id)}
          eventHandlers={{
            mouseover: () => onMarkerHover?.(r.gmap_id),
            mouseout:  () => onMarkerHover?.(null),
            click:     () => onMarkerClick?.(r.gmap_id),
          }}
        />
      ))}
    </MapContainer>
  )
}

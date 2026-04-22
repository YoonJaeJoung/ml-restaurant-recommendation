import { useEffect, useState } from 'react'
import MapView from '../components/MapView.jsx'
import Spinner from '../components/Spinner.jsx'
import Detail  from './Detail.jsx'
import { api } from '../api/client.js'

export default function BrowseAll({ selectedId, onSelectResult }) {
  const [points, setPoints] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    let cancelled = false
    api.browse()
      .then(d => { if (!cancelled) setPoints(d.points) })
      .catch(e => { if (!cancelled) setErr(e.message) })
    return () => { cancelled = true }
  }, [])

  return (
    <div className="results-root">
      <div className="map-layer">
        <MapView
          mode="browse"
          browsePoints={points || []}
          onBrowseClick={onSelectResult}
        />
      </div>

      <aside className="sidebar" style={{ width: 320 }}>
        <div className="sidebar-sticky-head" style={{ padding: '12px 16px' }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Browse all restaurants</h3>
          <p className="mono-meta" style={{ marginTop: 4 }}>
            {points ? `${points.length.toLocaleString()} pins on the map` : 'Loading…'}
          </p>
        </div>
        <div className="sidebar-body" style={{ padding: 18, fontSize: 13, color: 'var(--muted-strong)', lineHeight: 1.55 }}>
          <p>Zoom in to resolve individual restaurants. Click a pin for the detail panel.</p>
          <p style={{ marginTop: 14 }}>Clusters expand as you zoom; at high zoom each dot becomes a single restaurant.</p>
          {err && <p style={{ color: '#b00020' }}>{err}</p>}
        </div>
      </aside>

      {selectedId && (
        <Detail
          variant="panel"
          gmapId={selectedId}
          onBack={() => onSelectResult?.(null)}
          closeLabel="✕ Close"
        />
      )}

      {!points && !err && <Spinner label="Loading map" />}
    </div>
  )
}

import { useState } from 'react'

const OPTIONS = [
  { key: 'vegetarian', label: 'Vegetarian' },
  { key: 'halal',      label: 'Halal'      },
]

// `selected` is an array of keys; empty / null = no dietary filter.
export default function DietaryFilter({ selected, onChange }) {
  const [helpOpen, setHelpOpen] = useState(false)
  const active = Array.isArray(selected) ? selected : []

  const toggle = (key) => {
    const set = new Set(active)
    if (set.has(key)) set.delete(key); else set.add(key)
    onChange(Array.from(set))
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        <span className="mono-label sublabel" style={{ marginBottom: 0 }}>Dietary preference</span>
        <span className="experimental-tag">Experimental</span>
        <button
          type="button"
          className="info-btn"
          onClick={() => setHelpOpen(o => !o)}
          aria-label="What does this filter do?"
          title="What does this filter do?"
        >?</button>
      </div>
      <div className="day-row">
        {OPTIONS.map(({ key, label }) => (
          <button
            key={key}
            className={'day-chip' + (active.includes(key) ? ' active' : '')}
            onClick={() => toggle(key)}
          >{label}</button>
        ))}
      </div>
      {helpOpen && (
        <p className="mono-meta dietary-help">
          This filter only keeps restaurants Google has explicitly labeled as Vegetarian or Halal,
          which dramatically shrinks the result set — most matching places will be filtered out.
          For better coverage, just include &ldquo;vegetarian&rdquo; or &ldquo;halal&rdquo; in your
          query instead and let the semantic search handle it.
        </p>
      )}
    </div>
  )
}

import { useState } from 'react'
import { buildQueryFromToggles } from '../lib/queryBuilder.js'

// Mirrors the 4 questions in src/10_query_construction.py exactly.
const QUESTIONS = [
  {
    key: 'cuisine',
    label: 'Any cuisine preference?',
    options: ['Italian', 'Japanese / Sushi', 'Chinese', 'Mexican', 'Indian',
              'Seafood', 'American', 'Mediterranean', 'No preference'],
  },
  {
    key: 'vibe',
    label: 'What vibe are you looking for?',
    options: ['Cozy and intimate', 'Lively and fun', 'Quiet and relaxed',
              'Upscale and fancy', 'Casual and laid-back', 'Outdoor seating'],
  },
  {
    key: 'occasion',
    label: "What's the occasion?",
    options: ['Date night', 'Family dinner', 'Lunch with coworkers',
              'Catching up with friends', 'Solo meal', 'Celebration'],
  },
  {
    key: 'priority',
    label: 'Any other priorities?',
    options: ['Great cocktails', 'Good for groups', 'Late night',
              'Quick and easy', 'Vegetarian friendly', 'Good brunch', 'None'],
  },
]

// `onChange(query, toggles)` is called every time a chip is clicked so the parent
// can live-update the search input. `onCancel` restores the prior query.
// `onSearch` fires the search with the current toggles + query.
export default function InspireBuilder({ initialQuery, initialToggles, onChange, onCancel, onSearch }) {
  const [toggles, setToggles] = useState(initialToggles || {
    occasion: null, vibe: null, cuisine: null, priority: null
  })

  const set = (key, val) => {
    const next = { ...toggles, [key]: toggles?.[key] === val ? null : val }
    setToggles(next)
    onChange?.(buildQueryFromToggles(next), next)
  }

  return (
    <div className="inspire-body">
      <h3>Build a query from a few picks</h3>
      {QUESTIONS.map((q) => (
        <div key={q.key} style={{ marginBottom: 12 }}>
          <div className="mono-label sublabel">{q.label}</div>
          <div className="toggle-row">
            {q.options.map((opt) => (
              <button
                key={opt}
                className={'toggle-chip' + (toggles?.[q.key] === opt ? ' active' : '')}
                onClick={() => set(q.key, opt)}
              >{opt}</button>
            ))}
          </div>
        </div>
      ))}
      <div className="inspire-actions">
        <button className="btn ghost" onClick={onCancel}>Cancel</button>
        <button className="btn primary" onClick={() => onSearch?.(toggles)}>Search</button>
      </div>
    </div>
  )
}

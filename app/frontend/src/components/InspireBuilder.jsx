import { useState } from 'react'
import { buildQueryFromToggles } from '../lib/queryBuilder.js'

// Mirrors the 4 questions in src/10_query_construction.py exactly.
const PRIORITY_BY_TIME = {
  breakfast: ['Good coffee', 'Quick and easy', 'Vegetarian friendly', 'Good brunch', 'Quiet and relaxed', 'None'],
  lunch:     ['Quick and easy', 'Good for groups', 'Vegetarian friendly', 'Outdoor seating', 'None'],
  dinner:    ['Great cocktails', 'Good for groups', 'Late night', 'Vegetarian friendly', 'Upscale and fancy', 'None'],
  anytime:   ['Great cocktails', 'Good for groups', 'Late night', 'Quick and easy', 'Vegetarian friendly', 'Good brunch', 'None'],
}

function getTimeSlot(visitDate, anyTime) {
  if (anyTime || !visitDate) return 'anytime'
  const hour = visitDate.getHours()
  if (hour >= 6 && hour < 11)  return 'breakfast'
  if (hour >= 11 && hour < 16) return 'lunch'
  if (hour >= 16 && hour < 23) return 'dinner'
  return 'anytime'
}

const BASE_QUESTIONS = [
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
]
// `onChange(query, toggles)` is called every time a chip is clicked so the parent
// can live-update the search input. `onCancel` restores the prior query.
// `onSearch` fires the search with the current toggles + query.
export default function InspireBuilder({ initialQuery, initialToggles, visitDate, anyTime, onChange, onCancel, onSearch }) {
  const [toggles, setToggles] = useState(initialToggles || {
    occasion: null, vibe: null, cuisine: null, priority: []
  })

  const timeSlot = getTimeSlot(visitDate, anyTime)
  const priorityOptions = PRIORITY_BY_TIME[timeSlot]

  const questions = [
    ...BASE_QUESTIONS,
    {
      key: 'priority',
      label: 'Any other priorities?',
      options: priorityOptions,
    },
  ]

  const set = (key, val) => {
    let next
    if (key === 'priority') {
      const current = toggles.priority || []
      const already = current.includes(val)
      const updated = already ? current.filter(v => v !== val) : [...current, val]
      next = { ...toggles, priority: updated }
    } else {
      next = { ...toggles, [key]: toggles?.[key] === val ? null : val }
      if (next.priority && next.priority.some(p => !priorityOptions.includes(p))) {
        next.priority = next.priority.filter(p => priorityOptions.includes(p))
      }
    }
    setToggles(next)
    onChange?.(buildQueryFromToggles(next), next)
  }

  return (
    <div className="inspire-body">
      <h3>Build a query from a few picks</h3>
      {questions.map((q) => (
        <div key={q.key} style={{ marginBottom: 12 }}>
          <div className="mono-label sublabel">{q.label}</div>
          <div className="toggle-row">
            {q.options.map((opt) => (
              <button
                key={opt}
                className={'toggle-chip' + (
                  q.key === 'priority'
                    ? (toggles?.priority || []).includes(opt) ? ' active' : ''
                    : toggles?.[q.key] === opt ? ' active' : ''
                )}
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
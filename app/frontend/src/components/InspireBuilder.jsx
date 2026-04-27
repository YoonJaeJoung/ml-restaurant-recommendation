import { useEffect, useMemo, useState } from 'react'
import { buildQueryFromToggles } from '../lib/queryBuilder.js'

// Mirrors the 4 questions in src/10_query_construction.py exactly.
// `priority` is multi-select and depends on the time-of-day filter.
const PRIORITY_BY_TIME = {
  breakfast: ['Good coffee', 'Quick and easy', 'Vegetarian friendly', 'Good brunch', 'Quiet and relaxed', 'None'],
  lunch:     ['Quick and easy', 'Good for groups', 'Vegetarian friendly', 'Outdoor seating', 'None'],
  dinner:    ['Great cocktails', 'Good for groups', 'Late night', 'Vegetarian friendly', 'Upscale and fancy', 'None'],
  anytime:   ['Great cocktails', 'Good for groups', 'Late night', 'Quick and easy', 'Vegetarian friendly', 'Good brunch', 'None'],
}

// `occasion` is single-select and also varies by time slot — Date night and
// Family dinner don't make sense at 9 AM, Solo breakfast doesn't make sense
// at 8 PM, etc. Mirrors the time-aware shape of `priority`.
const OCCASION_BY_TIME = {
  breakfast: ['Solo breakfast', 'Catching up with friends', 'Lunch with coworkers', 'Quick bite'],
  lunch:     ['Lunch with coworkers', 'Catching up with friends', 'Solo meal', 'Family lunch', 'Quick bite'],
  dinner:    ['Date night', 'Family dinner', 'Catching up with friends', 'Solo meal', 'Celebration'],
  anytime:   ['Date night', 'Family dinner', 'Lunch with coworkers',
              'Catching up with friends', 'Solo meal', 'Celebration'],
}

function getTimeSlot(visitDate, anyTime) {
  if (anyTime || !visitDate) return 'anytime'
  const hour = visitDate.getHours()
  if (hour >= 6  && hour < 11) return 'breakfast'
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
]

// Coerce whatever shape `priority` arrives in (null / string / array) into a clean array.
function asPriorityArray(p) {
  if (Array.isArray(p)) return p
  if (typeof p === 'string' && p) return [p]
  return []
}

// `onChange(query, toggles)` is called every time a chip is clicked so the parent
// can live-update the search input. `onCancel` restores the prior query.
// `onSearch` fires the search with the current toggles + query.
export default function InspireBuilder({ initialQuery, initialToggles, visitDate, anyTime, onChange, onCancel, onSearch }) {
  const [toggles, setToggles] = useState(() => ({
    occasion: initialToggles?.occasion ?? null,
    vibe:     initialToggles?.vibe     ?? null,
    cuisine:  initialToggles?.cuisine  ?? null,
    priority: asPriorityArray(initialToggles?.priority),
  }))

  const timeSlot = getTimeSlot(visitDate, anyTime)
  const priorityOptions = useMemo(() => PRIORITY_BY_TIME[timeSlot], [timeSlot])
  const occasionOptions = useMemo(() => OCCASION_BY_TIME[timeSlot], [timeSlot])

  // When the time filter changes, drop any stale priority/occasion picks that
  // aren't valid for the new slot — otherwise hidden selections silently leak
  // into the search query.
  useEffect(() => {
    setToggles(prev => {
      const cleanedPriority = asPriorityArray(prev.priority).filter(p => priorityOptions.includes(p))
      const cleanedOccasion = prev.occasion && occasionOptions.includes(prev.occasion)
        ? prev.occasion
        : null
      const priorityChanged = cleanedPriority.length !== asPriorityArray(prev.priority).length
      const occasionChanged = cleanedOccasion !== prev.occasion
      if (!priorityChanged && !occasionChanged) return prev
      const next = { ...prev, priority: cleanedPriority, occasion: cleanedOccasion }
      onChange?.(buildQueryFromToggles(next), next)
      return next
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeSlot])

  const togglePriority = (val) => {
    const current = asPriorityArray(toggles.priority)
    if (val === 'None') {
      // "None" is a single-select escape hatch — picking it clears the rest;
      // picking it again clears everything.
      const next = { ...toggles, priority: current.includes('None') ? [] : ['None'] }
      setToggles(next); onChange?.(buildQueryFromToggles(next), next)
      return
    }
    const without = current.filter(v => v !== 'None')
    const updated = without.includes(val)
      ? without.filter(v => v !== val)
      : [...without, val]
    const next = { ...toggles, priority: updated }
    setToggles(next); onChange?.(buildQueryFromToggles(next), next)
  }

  const setSingle = (key, val) => {
    const next = { ...toggles, [key]: toggles?.[key] === val ? null : val }
    setToggles(next); onChange?.(buildQueryFromToggles(next), next)
  }

  const isActive = (key, opt) =>
    key === 'priority'
      ? asPriorityArray(toggles.priority).includes(opt)
      : toggles?.[key] === opt

  const questions = [
    ...BASE_QUESTIONS,
    {
      key: 'occasion',
      label: `What's the occasion? (${timeSlot})`,
      options: occasionOptions,
    },
    {
      key: 'priority',
      label: `Any other priorities? (${timeSlot} — pick any)`,
      options: priorityOptions,
    },
  ]

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
                className={'toggle-chip' + (isActive(q.key, opt) ? ' active' : '')}
                onClick={() => q.key === 'priority' ? togglePriority(opt) : setSingle(q.key, opt)}
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

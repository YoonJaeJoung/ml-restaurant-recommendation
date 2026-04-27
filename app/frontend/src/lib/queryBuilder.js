// Mirrors src/10_query_construction.py (and backend query_builder.py).
// Order: cuisine → vibe → occasion → priority.
// `priority` is multi-select (array); we tolerate string/null for safety.
export function buildQueryFromToggles(t) {
  if (!t) return ''
  const parts = []
  if (t.cuisine && t.cuisine !== 'No preference') parts.push(t.cuisine)
  if (t.vibe) parts.push(t.vibe)
  if (t.occasion) parts.push(t.occasion)
  const priorities = Array.isArray(t.priority)
    ? t.priority
    : (t.priority ? [t.priority] : [])
  const filtered = priorities.filter(p => p && p !== 'None')
  if (filtered.length > 0) parts.push(filtered.join(' '))
  return parts.join(' ')
}

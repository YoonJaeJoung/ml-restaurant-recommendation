// Mirrors src/10_query_construction.py (and backend query_builder.py).
// Order: cuisine → vibe → occasion → priority.
export function buildQueryFromToggles(t) {
  if (!t) return ''
  const parts = []
  if (t.cuisine && t.cuisine !== 'No preference') parts.push(t.cuisine)
  if (t.vibe) parts.push(t.vibe)
  if (t.occasion) parts.push(t.occasion)
  if (t.priority && t.priority !== 'None') parts.push(t.priority)
  return parts.join(' ')
}

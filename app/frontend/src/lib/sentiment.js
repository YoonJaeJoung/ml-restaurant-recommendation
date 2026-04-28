// Map a rounded 1-5 score to a Material Symbols sentiment glyph name.
// Used by both Detail.jsx (per-aspect cells + overall) and ResultCard.jsx
// (right-side score cluster) so the smiley reflects the same value everywhere.
export const SENTIMENT_BY_ROUND = {
  1: 'sentiment_extremely_dissatisfied',
  2: 'sentiment_frustrated',
  3: 'sentiment_neutral',
  4: 'sentiment_satisfied',
  5: 'sentiment_very_satisfied',
}

export function sentimentName(scoreFive) {
  if (scoreFive == null) return null
  const r = Math.max(1, Math.min(5, Math.round(scoreFive)))
  return SENTIMENT_BY_ROUND[r]
}

// Thin wrapper around fetch(). Uses Vite's dev proxy in development so we
// can hit `/api/...` directly without knowing the backend URL. In production
// you'd flip API_BASE to the actual backend origin.

const API_BASE = import.meta.env.VITE_API_BASE || ''

async function req(method, path, body) {
  const res = await fetch(API_BASE + path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    let detailStr
    try {
      const j = await res.json()
      const d = j.detail
      if (typeof d === 'string') {
        detailStr = d
      } else if (Array.isArray(d)) {
        // FastAPI 422 body: [{loc:[...], msg:"...", type:"..."}]
        detailStr = d.map(e => {
          const loc = Array.isArray(e.loc) ? e.loc.slice(1).join('.') : e.loc
          return `${loc || 'body'}: ${e.msg || JSON.stringify(e)}`
        }).join('; ')
      } else {
        detailStr = JSON.stringify(d)
      }
    } catch {
      detailStr = res.statusText
    }
    throw new Error(`${res.status} ${res.statusText}: ${detailStr}`)
  }
  return res.json()
}

export const api = {
  search:  (payload)               => req('POST', '/api/search', payload),
  detail:  (gmapId)                => req('GET',  `/api/restaurant/${encodeURIComponent(gmapId)}`),
  reviews: (gmapId, page, size)    => req('GET',  `/api/restaurant/${encodeURIComponent(gmapId)}/reviews?page=${page}&page_size=${size}`),
  browse:  ()                      => req('GET',  '/api/browse'),
  health:  ()                      => req('GET',  '/api/health'),
}

import { useEffect, useState } from 'react'

// Times Square — fallback if geolocation denied/unavailable.
export const NYC_FALLBACK = { lat: 40.7580, lon: -73.9855 }

// Gated geolocation: only prompts the browser permission when `enabled === true`.
// This lets us defer the popup until the user explicitly asks for "Search nearby",
// per item #8 in the plan.
export function useGeolocation(enabled = true) {
  const [pos, setPos] = useState(null)          // { lat, lon, fromFallback }
  const [asked, setAsked] = useState(false)

  useEffect(() => {
    if (!enabled || asked) return
    setAsked(true)
    if (!('geolocation' in navigator)) {
      setPos({ ...NYC_FALLBACK, fromFallback: true })
      return
    }
    navigator.geolocation.getCurrentPosition(
      (p) => setPos({ lat: p.coords.latitude, lon: p.coords.longitude, fromFallback: false }),
      ()  => setPos({ ...NYC_FALLBACK, fromFallback: true }),
      { timeout: 5000, enableHighAccuracy: false },
    )
  }, [enabled, asked])

  return pos
}

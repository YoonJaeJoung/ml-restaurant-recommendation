// Zero-dep inline SVG icons. Stroke + fill use `currentColor` so CSS can drive them.
// Based on Lucide (MIT) — hand-ported to avoid adding the lucide-react dependency.

function make(paths, { viewBox = '0 0 24 24', strokeWidth = 1.8, fill = 'none' } = {}) {
  return function Icon({ size = 16, className = '', title, ...rest }) {
    return (
      <svg
        width={size}
        height={size}
        viewBox={viewBox}
        fill={fill}
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
        aria-hidden={title ? undefined : true}
        role={title ? 'img' : undefined}
        {...rest}
      >
        {title && <title>{title}</title>}
        {paths}
      </svg>
    )
  }
}

// ── App-wide / nav ────────────────────────────────────────────────────
export const IconArrowLeft = make(
  <path d="M19 12H5M12 19l-7-7 7-7" />
)

export const IconChevronDown = make(
  <path d="M6 9l6 6 6-6" />
)

export const IconChevronUp = make(
  <path d="M18 15l-6-6-6 6" />
)

export const IconHelp = make(
  <>
    <circle cx="12" cy="12" r="10" />
    <path d="M9.1 9a3 3 0 015.8 1c0 2-3 3-3 3M12 17h.01" />
  </>
)

export const IconClose = make(
  <path d="M18 6L6 18M6 6l12 12" />
)

export const IconSearch = make(
  <>
    <circle cx="11" cy="11" r="7" />
    <path d="M21 21l-4.3-4.3" />
  </>
)

// GitHub octocat — fill-based (Primer v1)
export const IconGithub = make(
  <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />,
  { viewBox: '0 0 16 16', fill: 'currentColor', strokeWidth: 0 }
)

// ── Score / sort metrics ──────────────────────────────────────────────
// Overall (bullseye)
export const IconTarget = make(
  <>
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" />
  </>
)

// Google rating (star)
export const IconStar = make(
  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />,
  { fill: 'currentColor', strokeWidth: 0 }
)

// Food (utensils / fork + knife)
export const IconUtensils = make(
  <>
    <path d="M3 2v7a2 2 0 002 2h2a2 2 0 002-2V2M7 11v11M17 2v20M21 5a3 3 0 00-3-3v10a3 3 0 003-3V5z" />
  </>
)

// Service (smile face)
export const IconService = make(
  <>
    <circle cx="12" cy="12" r="10" />
    <path d="M8 14s1.5 2 4 2 4-2 4-2" />
    <line x1="9"  y1="9" x2="9.01"  y2="9" />
    <line x1="15" y1="9" x2="15.01" y2="9" />
  </>
)

// Wait time (clock)
export const IconClock = make(
  <>
    <circle cx="12" cy="12" r="10" />
    <path d="M12 6v6l4 2" />
  </>
)

// Price (dollar sign)
export const IconDollar = make(
  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 100 7h5a3.5 3.5 0 110 7H6" />
)

// ── Map controls ──────────────────────────────────────────────────────
export const IconPlus = make(
  <path d="M12 5v14M5 12h14" />
)

export const IconMinus = make(
  <path d="M5 12h14" />
)

// Current location (crosshair)
export const IconLocate = make(
  <>
    <circle cx="12" cy="12" r="3" />
    <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
  </>
)

// Draw polygon
export const IconPolygon = make(
  <>
    <polygon points="12 3 21 9 18 20 6 20 3 9 12 3" />
  </>
)

// Draw rectangle
export const IconRectangle = make(
  <rect x="3" y="5" width="18" height="14" rx="1" />
)

// Viewport capture (corner brackets)
export const IconViewport = make(
  <>
    <path d="M4 8V4h4M20 8V4h-4M4 16v4h4M20 16v4h-4" />
  </>
)

// Counter-clockwise arrow (used by "Revert to overall ranking").
export const IconUndo = make(
  <>
    <path d="M3 7v6h6" />
    <path d="M21 17a9 9 0 0 0-15-6.7L3 13" />
  </>
)

// Material Symbols ligature wrapper. Use for Google's pre-drawn glyphs
// (sentiment_*, concierge, etc.). The font is loaded via index.html.
export function MS({ name, size = 18, className = '' }) {
  return (
    <span
      className={'material-symbols-outlined ' + className}
      style={{
        fontSize: size,
        lineHeight: 1,
        fontVariationSettings: '"opsz" 24, "wght" 400, "FILL" 0, "GRAD" 0',
        verticalAlign: 'middle',
      }}
    >{name}</span>
  )
}

// panels.jsx — reusable UI pieces for FML. Glass panels, cards, chips, etc.

const T = {
  // Typography / animation tokens
  font: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", Inter, system-ui, sans-serif',
  mono: 'ui-monospace, "SF Mono", Menlo, Consolas, monospace',
  ease: 'cubic-bezier(.22,.61,.36,1)',  // ease-out-ish
  dur: 160,
};

// Theme tokens for everything except the map (map has its own)
function useThemeVars(theme) {
  if (theme === 'dark') return {
    bg: '#0A0A0A',
    panel: 'rgba(20,20,22,0.72)',
    panelBorder: 'rgba(255,255,255,0.08)',
    text: '#FAFAFA',
    muted: '#9CA3AF',
    border: 'rgba(255,255,255,0.06)',
    borderStrong: 'rgba(255,255,255,0.12)',
    accent: '#818CF8',
    surface: 'rgba(255,255,255,0.04)',
    surfaceHover: 'rgba(255,255,255,0.08)',
    inputBg: 'rgba(255,255,255,0.04)',
    chip: 'rgba(255,255,255,0.06)',
    card: 'rgba(255,255,255,0.02)',
    divider: 'rgba(255,255,255,0.06)',
  };
  return {
    bg: '#FFFFFF',
    panel: 'rgba(255,255,255,0.78)',
    panelBorder: 'rgba(17,24,39,0.08)',
    text: '#111827',
    muted: '#6B7280',
    border: '#E5E7EB',
    borderStrong: 'rgba(17,24,39,0.18)',
    accent: '#1E3A8A',
    surface: 'rgba(17,24,39,0.03)',
    surfaceHover: 'rgba(17,24,39,0.06)',
    inputBg: 'rgba(17,24,39,0.02)',
    chip: 'rgba(17,24,39,0.05)',
    card: 'rgba(255,255,255,0.6)',
    divider: 'rgba(17,24,39,0.08)',
  };
}

// Floating glass panel
function GlassPanel({ theme, children, style, ...rest }) {
  const c = useThemeVars(theme);
  return (
    <div
      style={{
        background: c.panel,
        backdropFilter: 'blur(22px) saturate(1.6)',
        WebkitBackdropFilter: 'blur(22px) saturate(1.6)',
        border: `1px solid ${c.panelBorder}`,
        borderRadius: 14,
        boxShadow: theme === 'dark'
          ? '0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px rgba(0,0,0,0.4)'
          : '0 1px 0 rgba(255,255,255,0.8) inset, 0 6px 24px rgba(17,24,39,0.08)',
        ...style,
      }}
      {...rest}
    >{children}</div>
  );
}

// Single-line chip
function Chip({ theme, children, onClick, active }) {
  const c = useThemeVars(theme);
  const [hover, setHover] = React.useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        fontFamily: T.mono, fontSize: 11, letterSpacing: 0.3,
        padding: '5px 9px', borderRadius: 4,
        background: active ? c.accent : (hover ? c.surfaceHover : c.chip),
        color: active ? (theme === 'dark' ? '#0A0A0A' : '#FFFFFF') : c.text,
        border: 'none', cursor: onClick ? 'pointer' : 'default',
        transition: `all ${T.dur}ms ${T.ease}`,
        whiteSpace: 'nowrap',
      }}
    >{children}</button>
  );
}

// Rating stars — subtle, tabular
function Rating({ value, theme, size = 12 }) {
  const c = useThemeVars(theme);
  return (
    <span style={{
      fontFamily: T.mono, fontSize: size, color: c.text,
      fontVariantNumeric: 'tabular-nums', fontWeight: 500,
    }}>
      {value.toFixed(1)}
      <span style={{ color: c.muted, marginLeft: 3 }}>★</span>
    </span>
  );
}

// Similarity bar — 1px line, fills proportionally
function SimilarityBar({ value, theme }) {
  const c = useThemeVars(theme);
  return (
    <div style={{
      height: 1, background: c.divider, width: '100%', overflow: 'hidden',
    }}>
      <div style={{
        height: '100%',
        width: `${Math.round(value * 100)}%`,
        background: c.accent,
        transition: `width 400ms ${T.ease}`,
      }} />
    </div>
  );
}

// Restaurant result card used in the results panel
function ResultCard({ restaurant, theme, hovered, onHover, onClick, showRank }) {
  const c = useThemeVars(theme);
  const cluster = CLUSTERS[restaurant.cluster - 1];
  return (
    <div
      onMouseEnter={() => onHover && onHover(restaurant.id)}
      onMouseLeave={() => onHover && onHover(null)}
      onClick={onClick}
      style={{
        padding: '14px 16px',
        cursor: 'pointer',
        position: 'relative',
        background: hovered ? c.surfaceHover : 'transparent',
        borderLeft: `2px solid ${hovered ? c.accent : 'transparent'}`,
        transition: `all ${T.dur}ms ${T.ease}`,
      }}
    >
      {showRank && (
        <div style={{
          position: 'absolute', left: -2, top: 16,
          fontFamily: T.mono, fontSize: 10, color: c.muted,
          fontVariantNumeric: 'tabular-nums',
          transform: 'translateX(-22px)',
          width: 16, textAlign: 'right',
        }}>{String(restaurant.rank).padStart(2, '0')}</div>
      )}

      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 3 }}>
        <div style={{
          fontSize: 15, fontWeight: 500, color: c.text, letterSpacing: -0.15,
        }}>{restaurant.name}</div>
        <Rating value={restaurant.rating} theme={theme} />
      </div>

      <div style={{ fontSize: 12, color: c.muted, marginBottom: 10, display: 'flex', gap: 6, alignItems: 'center' }}>
        <span>{restaurant.neighborhood}</span>
        <span style={{ opacity: 0.5 }}>·</span>
        <span>{restaurant.borough}</span>
        <span style={{ opacity: 0.5 }}>·</span>
        <span style={{ fontFamily: T.mono, fontSize: 11 }}>{restaurant.price}</span>
      </div>

      {/* Cluster keywords */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
        {cluster.keywords.slice(0, 3).map(k => (
          <span key={k} style={{
            fontFamily: T.mono, fontSize: 10.5, color: c.muted, letterSpacing: 0.2,
          }}>{k}</span>
        )).reduce((acc, x, i) => {
          if (i > 0) acc.push(<span key={'s'+i} style={{ color: c.muted, opacity: 0.4 }}>/</span>);
          acc.push(x);
          return acc;
        }, [])}
      </div>

      {restaurant.similarity !== undefined && (
        <SimilarityBar value={restaurant.similarity} theme={theme} />
      )}
    </div>
  );
}

// Featured cluster card (Home / Discover)
function ClusterCard({ cluster, theme, onClick }) {
  const c = useThemeVars(theme);
  const [hover, setHover] = React.useState(false);
  const sample = RESTAURANTS.filter(r => r.cluster === cluster.id).slice(0, 2);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        padding: '18px 16px',
        cursor: 'pointer',
        borderTop: `1px solid ${c.divider}`,
        transition: `all ${T.dur}ms ${T.ease}`,
        background: hover ? c.surfaceHover : 'transparent',
      }}
    >
      {/* Typographic stack — type is the visual */}
      <div style={{ marginBottom: 12 }}>
        {cluster.keywords.map((k, i) => (
          <div key={k} style={{
            fontSize: i === 0 ? 22 : (i === 1 ? 18 : 15),
            fontWeight: i === 0 ? 600 : (i === 1 ? 500 : 400),
            color: i === 0 ? c.text : (i === 1 ? c.text : c.muted),
            letterSpacing: -0.4,
            lineHeight: 1.1,
            opacity: i === 0 ? 1 : (i === 1 ? 0.85 : 0.6),
          }}>{k}</div>
        ))}
      </div>

      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        fontFamily: T.mono, fontSize: 10.5, color: c.muted, letterSpacing: 0.2,
        marginBottom: 8,
      }}>
        <span style={{ fontVariantNumeric: 'tabular-nums' }}>
          {String(cluster.size).padStart(3, '0')} places
        </span>
        <span>{cluster.borough.toLowerCase()}</span>
        <Rating value={cluster.rating} theme={theme} size={11} />
      </div>

      <div style={{ fontSize: 11, color: c.muted, opacity: 0.7, fontStyle: 'italic' }}>
        e.g. {sample.map(s => s.name).join(', ')}
      </div>
    </div>
  );
}

Object.assign(window, { T, useThemeVars, GlassPanel, Chip, Rating, SimilarityBar, ResultCard, ClusterCard });

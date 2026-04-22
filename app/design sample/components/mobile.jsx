// mobile.jsx — mobile variants of the FML screens, shown in iPhone-sized frames on the canvas.
// These are presentation-only; they share the panel/screen components but lay them out as a bottom sheet.

function MobileFrame({ theme, sheetState = 'half', children, statusBar = true, overlay }) {
  const c = useThemeVars(theme);
  const sheetHeights = { peek: 120, half: 440, full: 740 };
  const sheetH = sheetHeights[sheetState];

  return (
    <div style={{
      width: 390, height: 844,
      position: 'relative', overflow: 'hidden',
      background: c.bg, color: c.text,
      fontFamily: T.font,
    }}>
      {/* Status bar */}
      {statusBar && (
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: 54,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 28px 0', zIndex: 20,
          fontFamily: T.font, fontSize: 15, fontWeight: 600, color: c.text,
        }}>
          <span>9:41</span>
          <span style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
            <svg width="18" height="12" viewBox="0 0 18 12" fill="currentColor"><rect x="0" y="6" width="3" height="6" rx="0.5"/><rect x="5" y="3.5" width="3" height="8.5" rx="0.5"/><rect x="10" y="1" width="3" height="11" rx="0.5"/></svg>
            <svg width="18" height="12" viewBox="0 0 18 12" fill="currentColor" opacity="0.9"><path d="M9 11.5c1.38 0 2.5-1.12 2.5-2.5s-1.12-2.5-2.5-2.5S6.5 7.62 6.5 9s1.12 2.5 2.5 2.5z" opacity="0.4"/><path d="M9 3c-2.6 0-5 .9-6.85 2.4l1.5 1.5c1.45-1.15 3.3-1.9 5.35-1.9s3.9.75 5.35 1.9l1.5-1.5C14 3.9 11.6 3 9 3z"/></svg>
            <div style={{ width: 22, height: 10, border: `1px solid ${c.text}`, borderRadius: 2.5, padding: 1 }}>
              <div style={{ width: '80%', height: '100%', background: c.text, borderRadius: 1 }} />
            </div>
          </span>
        </div>
      )}

      {/* Map underlay */}
      <div style={{ position: 'absolute', inset: 0 }}>
        <NYCMap dots={DOTS.slice(0, 6000)} restaurants={overlay?.results || []} theme={theme} dimmed={!!overlay?.dimmed} />
      </div>

      {/* Top controls */}
      <div style={{
        position: 'absolute', top: 62, right: 16, zIndex: 22,
        display: 'flex', flexDirection: 'column', gap: 8,
      }}>
        <div style={{
          width: 40, height: 40, borderRadius: 10,
          background: theme === 'dark' ? 'rgba(20,20,22,0.75)' : 'rgba(255,255,255,0.82)',
          backdropFilter: 'blur(18px)', WebkitBackdropFilter: 'blur(18px)',
          border: `1px solid ${c.panelBorder}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: c.text,
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5"/></svg>
        </div>
      </div>

      {/* Wordmark */}
      <div style={{
        position: 'absolute', top: 68, left: 22, zIndex: 22,
        fontFamily: T.mono, fontSize: 10, color: c.muted, letterSpacing: 3, textTransform: 'uppercase',
      }}>fml</div>

      {/* Bottom sheet */}
      <div style={{
        position: 'absolute', left: 0, right: 0, bottom: 0,
        height: sheetH,
        background: theme === 'dark' ? 'rgba(15,15,17,0.86)' : 'rgba(255,255,255,0.9)',
        backdropFilter: 'blur(28px) saturate(1.6)', WebkitBackdropFilter: 'blur(28px) saturate(1.6)',
        borderTopLeftRadius: 16, borderTopRightRadius: 16,
        borderTop: `1px solid ${c.panelBorder}`,
        boxShadow: '0 -8px 32px rgba(0,0,0,0.12)',
        transition: `height 280ms ${T.ease}`,
        display: 'flex', flexDirection: 'column',
        overflow: 'hidden',
        zIndex: 25,
      }}>
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 8, paddingBottom: 4 }}>
          <div style={{ width: 36, height: 4, borderRadius: 2, background: c.borderStrong }} />
        </div>
        {children}
      </div>

      {/* Home indicator */}
      <div style={{
        position: 'absolute', bottom: 8, left: '50%', transform: 'translateX(-50%)',
        width: 134, height: 5, borderRadius: 3,
        background: c.text, opacity: 0.85, zIndex: 30,
      }} />
    </div>
  );
}

// Mobile HOME
function MobileHome({ theme }) {
  const c = useThemeVars(theme);
  const featured = [CLUSTERS[0], CLUSTERS[6], CLUSTERS[4]];
  return (
    <MobileFrame theme={theme} sheetState="half">
      <div style={{ padding: '4px 20px 12px' }}>
        {/* Search bar */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '11px 14px',
          background: c.inputBg, border: `1px solid ${c.border}`, borderRadius: 10,
          marginBottom: 16,
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={c.muted} strokeWidth="1.8"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          <span style={{ color: c.muted, fontSize: 14 }}>Search by mood, cuisine, vibe…</span>
        </div>

        <div style={{
          fontFamily: T.mono, fontSize: 10, letterSpacing: 2.2, color: c.muted,
          textTransform: 'uppercase', marginBottom: 6,
        }}>Explore NYC</div>
        <div style={{
          fontSize: 22, fontWeight: 600, color: c.text, letterSpacing: -0.5,
          lineHeight: 1.15, marginBottom: 10,
        }}>Seven thousand<br/>ways to eat.</div>
      </div>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {featured.map(cl => (<ClusterCard key={cl.id} cluster={cl} theme={theme} />))}
      </div>
    </MobileFrame>
  );
}

// Mobile RESULTS
function MobileResults({ theme }) {
  const c = useThemeVars(theme);
  const { restaurants: results, clusters } = searchRestaurants('cozy italian outdoor');
  return (
    <MobileFrame theme={theme} sheetState="full" overlay={{ results, dimmed: true }}>
      <div style={{ padding: '4px 20px 10px' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '11px 14px',
          background: c.inputBg, border: `1px solid ${c.accent}`, borderRadius: 10,
          marginBottom: 14,
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={c.accent} strokeWidth="1.8"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          <span style={{ color: c.text, fontSize: 14 }}>cozy italian outdoor</span>
        </div>
        <div style={{
          fontFamily: T.mono, fontSize: 10, letterSpacing: 2, color: c.muted,
          textTransform: 'uppercase', marginBottom: 6,
        }}>Matched</div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
          {clusters.map(cl => (
            <div key={cl.id} style={{
              display: 'inline-flex', alignItems: 'center', gap: 5,
              padding: '4px 8px', background: c.chip, borderRadius: 3,
            }}>
              <span style={{ fontFamily: T.mono, fontSize: 10, color: c.muted, fontVariantNumeric: 'tabular-nums' }}>#{String(cl.id).padStart(2,'0')}</span>
              <span style={{ fontFamily: T.mono, fontSize: 10, color: c.text }}>{cl.keywords.slice(0,2).join(' · ')}</span>
            </div>
          ))}
        </div>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', paddingLeft: 24 }}>
        {results.slice(0, 6).map(r => (
          <ResultCard key={r.id} restaurant={r} theme={theme} showRank />
        ))}
      </div>
    </MobileFrame>
  );
}

// Mobile DETAIL
function MobileDetail({ theme }) {
  const c = useThemeVars(theme);
  const r = RESTAURANTS[0];
  const cluster = CLUSTERS[r.cluster - 1];
  return (
    <div style={{
      width: 390, height: 844, position: 'relative', overflow: 'hidden',
      background: c.bg, color: c.text, fontFamily: T.font,
    }}>
      {/* Status bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 54,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '16px 28px 0', zIndex: 20,
        fontFamily: T.font, fontSize: 15, fontWeight: 600, color: c.text,
      }}>
        <span>9:41</span>
        <span style={{ fontFamily: T.mono, fontSize: 11 }}>●●●</span>
      </div>

      {/* Back bar */}
      <div style={{
        position: 'absolute', top: 54, left: 0, right: 0, zIndex: 15,
        padding: '10px 20px', borderBottom: `1px solid ${c.divider}`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <span style={{ fontFamily: T.mono, fontSize: 11, color: c.text }}>← Back</span>
        <span style={{ fontFamily: T.mono, fontSize: 10, color: c.muted, letterSpacing: 2, textTransform: 'uppercase' }}>fml /r/{r.id}</span>
      </div>

      <div style={{ padding: '106px 24px 80px', height: '100%', overflowY: 'auto' }}>
        <div style={{
          fontFamily: T.mono, fontSize: 10, letterSpacing: 2, color: c.accent,
          textTransform: 'uppercase', marginBottom: 12,
        }}>#{String(cluster.id).padStart(2,'0')} · {cluster.keywords[0]}</div>
        <h1 style={{ fontSize: 36, fontWeight: 600, letterSpacing: -1.1, lineHeight: 1, margin: '0 0 14px' }}>{r.name}</h1>
        <div style={{ fontSize: 13, color: c.muted, marginBottom: 24, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ color: c.text }}>{r.neighborhood}</span>
          <span style={{ opacity: 0.4 }}>·</span>
          <Rating value={r.rating} theme={theme} size={13} />
          <span style={{ opacity: 0.4 }}>·</span>
          <span style={{ fontFamily: T.mono }}>{r.price}</span>
        </div>

        <div style={{
          height: 200, marginBottom: 30,
          background: `repeating-linear-gradient(45deg, ${c.surface}, ${c.surface} 6px, transparent 6px, transparent 12px)`,
          border: `1px solid ${c.divider}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: T.mono, fontSize: 10, color: c.muted, letterSpacing: 1, textTransform: 'uppercase',
        }}>dining room</div>

        <div style={{
          fontFamily: T.mono, fontSize: 10, letterSpacing: 2, color: c.muted,
          textTransform: 'uppercase', marginBottom: 14,
        }}>This place belongs to</div>
        <div style={{ paddingTop: 14, borderTop: `1px solid ${c.divider}`, marginBottom: 30 }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: c.text, letterSpacing: -0.3, marginBottom: 6 }}>
            {cluster.keywords.join(' · ')}
          </div>
          <div style={{ fontSize: 12, color: c.muted }}>{cluster.size} places · mostly {cluster.borough}</div>
        </div>

        <div style={{ fontFamily: T.mono, fontSize: 10, letterSpacing: 2, color: c.muted, textTransform: 'uppercase', marginBottom: 14 }}>From the reviews</div>
        {REVIEWS.slice(0, 3).map((rv, i) => (
          <div key={i} style={{
            paddingLeft: 12, borderLeft: `1px solid ${c.divider}`,
            fontSize: 14, fontStyle: 'italic', lineHeight: 1.5,
            marginBottom: 16,
          }}>"{rv}"</div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { MobileFrame, MobileHome, MobileResults, MobileDetail });

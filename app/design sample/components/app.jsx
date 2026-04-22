// app.jsx — FML prototype orchestrator.
// Manages screen state, panel, theme, command palette, cluster explorer, search.

// Tweak defaults — theme toggle is the persisted tweak
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "light"
}/*EDITMODE-END*/;

function FMLApp() {
  // Persisted state via TWEAK defaults + localStorage
  const [theme, setTheme] = React.useState(() => {
    return localStorage.getItem('fml-theme') || TWEAK_DEFAULTS.theme;
  });
  React.useEffect(() => { localStorage.setItem('fml-theme', theme); }, [theme]);

  const c = useThemeVars(theme);

  // Screen state: 'home' | 'results' | 'detail'
  const [screen, setScreen] = React.useState(() => localStorage.getItem('fml-screen') || 'home');
  const [query, setQuery] = React.useState(() => localStorage.getItem('fml-query') || '');
  const [detailId, setDetailId] = React.useState(() => {
    const v = localStorage.getItem('fml-detail'); return v ? parseInt(v) : null;
  });

  React.useEffect(() => { localStorage.setItem('fml-screen', screen); }, [screen]);
  React.useEffect(() => { localStorage.setItem('fml-query', query); }, [query]);
  React.useEffect(() => {
    if (detailId) localStorage.setItem('fml-detail', String(detailId));
    else localStorage.removeItem('fml-detail');
  }, [detailId]);

  // Modal states
  const [explorerOpen, setExplorerOpen] = React.useState(false);
  const [cmdkOpen, setCmdkOpen] = React.useState(false);

  // Interaction
  const [hoveredId, setHoveredId] = React.useState(null);
  const [panelCollapsed, setPanelCollapsed] = React.useState(false);
  const resultsRef = React.useRef(null);

  // Recompute search results when query changes
  const { restaurants: results, clusters: matchedClusters } = React.useMemo(() => {
    if (!query.trim()) return { restaurants: [], clusters: [] };
    return searchRestaurants(query);
  }, [query]);

  // Keyboard shortcut: ⌘K
  React.useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCmdkOpen(o => !o);
      }
      if (e.key === 'Escape') {
        if (cmdkOpen) setCmdkOpen(false);
        else if (explorerOpen) setExplorerOpen(false);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [cmdkOpen, explorerOpen]);

  // Edit-mode protocol
  React.useEffect(() => {
    const onMsg = (e) => {
      if (e.data?.type === '__activate_edit_mode') setEditMode(true);
      if (e.data?.type === '__deactivate_edit_mode') setEditMode(false);
    };
    window.addEventListener('message', onMsg);
    window.parent.postMessage({ type: '__edit_mode_available' }, '*');
    return () => window.removeEventListener('message', onMsg);
  }, []);
  const [editMode, setEditMode] = React.useState(false);

  // Actions
  const runSearch = (q) => {
    setQuery(q);
    setScreen('results');
    setDetailId(null);
  };
  const openDetail = (r) => {
    setDetailId(r.id);
    setScreen('detail');
  };
  const backFromDetail = () => {
    setDetailId(null);
    setScreen(query.trim() ? 'results' : 'home');
  };
  const openCluster = (cl) => {
    // Treat a cluster click as a search for that cluster's keywords
    runSearch(cl.keywords.join(' '));
    setExplorerOpen(false);
  };
  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    window.parent.postMessage({ type: '__edit_mode_set_keys', edits: { theme: next } }, '*');
  };

  // Scroll hovered card into view when a map marker is clicked
  const markerClick = (id) => {
    setHoveredId(id);
    const r = results.find(x => x.id === id);
    if (r) {
      // flash highlight; if in a list, scroll
      const el = document.querySelector(`[data-rid="${id}"]`);
      if (el && resultsRef.current) {
        const top = el.offsetTop - 80;
        resultsRef.current.scrollTo({ top, behavior: 'smooth' });
      } else {
        openDetail(r);
      }
    }
  };

  const detail = detailId ? RESTAURANTS.find(r => r.id === detailId) : null;

  return (
    <div data-screen-label={`FML · ${theme}`} style={{
      position: 'fixed', inset: 0, background: c.bg, color: c.text,
      fontFamily: T.font, overflow: 'hidden',
      transition: `background 240ms ${T.ease}, color 240ms ${T.ease}`,
    }}>
      {/* Map stage — full-bleed */}
      <div style={{ position: 'absolute', inset: 0 }}>
        <NYCMap
          dots={DOTS}
          restaurants={screen === 'results' ? results : []}
          dimmed={screen === 'results'}
          theme={theme}
          hoveredId={hoveredId}
          onMarkerHover={setHoveredId}
          onMarkerClick={markerClick}
        />
      </div>

      {/* Top-right: theme toggle, cluster explorer, ⌘K */}
      <div style={{
        position: 'absolute', top: 16, right: 16, zIndex: 20,
        display: 'flex', gap: 8,
      }}>
        <TopButton theme={theme} onClick={() => setExplorerOpen(true)} label="Clusters" mono />
        <TopButton theme={theme} onClick={() => setCmdkOpen(true)} label="⌘K" mono />
        <ThemeToggle theme={theme} onClick={toggleTheme} />
      </div>

      {/* Wordmark — top-left, outside the panel */}
      <div style={{
        position: 'absolute', top: 24, left: 20, zIndex: 25,
        pointerEvents: 'none',
      }}>
        <div style={{
          fontFamily: T.mono, fontSize: 11, letterSpacing: 3.2, color: c.muted,
          textTransform: 'uppercase', marginBottom: 2,
        }}>fml</div>
      </div>

      {/* Left floating panel */}
      {screen !== 'detail' && (
        <GlassPanel
          theme={theme}
          style={{
            position: 'absolute', top: 60, left: 16, bottom: 16,
            width: panelCollapsed ? 56 : 380,
            overflow: 'hidden',
            transition: `width 280ms ${T.ease}`,
            display: 'flex', flexDirection: 'column',
          }}
        >
          {/* Collapse toggle */}
          <button
            onClick={() => setPanelCollapsed(x => !x)}
            aria-label="Collapse panel"
            style={{
              position: 'absolute', top: 12, right: 12, zIndex: 5,
              width: 24, height: 24, borderRadius: 4,
              background: c.surface, border: 'none', cursor: 'pointer',
              color: c.muted, fontFamily: T.mono, fontSize: 12,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >{panelCollapsed ? '›' : '‹'}</button>

          {panelCollapsed ? (
            <div style={{
              flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: T.mono, fontSize: 10, color: c.muted, letterSpacing: 2,
              writingMode: 'vertical-rl', textTransform: 'uppercase',
            }}>
              {screen === 'results' ? `${results.length} results` : 'Explore NYC'}
            </div>
          ) : (
            <>
              {/* Search bar */}
              <SearchBar
                theme={theme}
                value={query}
                onChange={setQuery}
                onSubmit={(v) => { if (v.trim()) { setQuery(v); setScreen('results'); } else { setScreen('home'); } }}
                onFocus={() => {}}
              />

              {/* Screen content */}
              <div ref={resultsRef} style={{ flex: 1, overflowY: 'auto', paddingBottom: 12 }}>
                {screen === 'results' && results.length > 0 ? (
                  <SearchResults
                    query={query} results={results} matchedClusters={matchedClusters}
                    theme={theme}
                    hoveredId={hoveredId}
                    onHover={setHoveredId}
                    onOpen={openDetail}
                  />
                ) : (
                  <HomeDiscover
                    theme={theme}
                    onCluster={openCluster}
                    onOpenExplorer={() => setExplorerOpen(true)}
                  />
                )}
              </div>
            </>
          )}
        </GlassPanel>
      )}

      {/* Attach data-rid to cards for scroll */}
      <style>{`
        @keyframes fmlCmdkIn {
          from { opacity: 0; transform: translateY(-8px) scale(0.98); }
          to { opacity: 1; transform: none; }
        }
        @keyframes fmlFadeIn { from { opacity: 0 } to { opacity: 1 } }
        @keyframes fmlSheetIn {
          from { transform: translateY(100%); } to { transform: none; }
        }
      `}</style>

      {/* Detail overlay */}
      {screen === 'detail' && detail && (
        <RestaurantDetail
          restaurant={detail}
          theme={theme}
          onBack={backFromDetail}
          onCluster={openCluster}
          onOpen={(r) => setDetailId(r.id)}
        />
      )}

      {/* Cluster explorer */}
      {explorerOpen && (
        <ClusterExplorer theme={theme} onClose={() => setExplorerOpen(false)} onCluster={openCluster} />
      )}

      {/* Command palette */}
      {cmdkOpen && (
        <CommandPalette
          theme={theme}
          onClose={() => setCmdkOpen(false)}
          onSearch={runSearch}
          onCluster={openCluster}
          onToggleTheme={toggleTheme}
        />
      )}

      {/* Hint bar — bottom-center */}
      {!cmdkOpen && !explorerOpen && screen !== 'detail' && (
        <div style={{
          position: 'absolute', bottom: 24, left: '50%', transform: 'translateX(-50%)',
          zIndex: 15,
          display: 'flex', gap: 14,
          fontFamily: T.mono, fontSize: 10, color: c.muted, letterSpacing: 0.5,
        }}>
          <GlassPanel theme={theme} style={{ padding: '8px 14px', display: 'flex', gap: 14, borderRadius: 999 }}>
            <span>⌘K for anything</span>
            <span style={{ opacity: 0.4 }}>·</span>
            <span onClick={() => setExplorerOpen(true)} style={{ cursor: 'pointer' }}>50 clusters</span>
          </GlassPanel>
        </div>
      )}
    </div>
  );
}

// Small top bar button
function TopButton({ theme, onClick, label, mono }) {
  const c = useThemeVars(theme);
  const [hover, setHover] = React.useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        padding: '8px 12px', height: 34,
        background: theme === 'dark'
          ? (hover ? 'rgba(30,30,32,0.85)' : 'rgba(20,20,22,0.72)')
          : (hover ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.78)'),
        backdropFilter: 'blur(22px) saturate(1.6)',
        WebkitBackdropFilter: 'blur(22px) saturate(1.6)',
        border: `1px solid ${c.panelBorder}`,
        borderRadius: 8,
        color: c.text,
        fontFamily: mono ? T.mono : T.font,
        fontSize: mono ? 11 : 12,
        letterSpacing: mono ? 0.5 : 0,
        cursor: 'pointer',
        transition: `all ${T.dur}ms ${T.ease}`,
      }}
    >{label}</button>
  );
}

function ThemeToggle({ theme, onClick }) {
  const c = useThemeVars(theme);
  const isDark = theme === 'dark';
  return (
    <button
      onClick={onClick}
      aria-label="Toggle theme"
      style={{
        padding: 0, width: 34, height: 34,
        background: isDark ? 'rgba(20,20,22,0.72)' : 'rgba(255,255,255,0.78)',
        backdropFilter: 'blur(22px) saturate(1.6)',
        WebkitBackdropFilter: 'blur(22px) saturate(1.6)',
        border: `1px solid ${c.panelBorder}`,
        borderRadius: 8,
        color: c.text, cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: `all 240ms ${T.ease}`,
      }}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        {isDark
          ? <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          : <g><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></g>
        }
      </svg>
    </button>
  );
}

function SearchBar({ theme, value, onChange, onSubmit, onFocus }) {
  const c = useThemeVars(theme);
  const [focused, setFocused] = React.useState(false);
  return (
    <div style={{ padding: '20px 18px 12px' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '11px 14px',
        background: c.inputBg,
        border: `1px solid ${focused ? c.accent : c.border}`,
        borderRadius: 10,
        transition: `border-color ${T.dur}ms ${T.ease}`,
      }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={c.muted} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>
        </svg>
        <input
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') onSubmit(e.target.value); }}
          onFocus={() => { setFocused(true); onFocus && onFocus(); }}
          onBlur={() => setFocused(false)}
          placeholder="Search by mood, cuisine, vibe…"
          style={{
            flex: 1, background: 'transparent', border: 'none', outline: 'none',
            fontFamily: T.font, fontSize: 14, color: c.text,
          }}
        />
        {value && (
          <button onClick={() => onChange('')} aria-label="Clear"
            style={{ background: 'transparent', border: 'none', color: c.muted, cursor: 'pointer', fontSize: 14 }}
          >✕</button>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { FMLApp });

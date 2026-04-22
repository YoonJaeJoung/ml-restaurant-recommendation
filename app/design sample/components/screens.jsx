// screens.jsx — the screens of the FML prototype.
// Each screen renders into a Stage provided by app.jsx (the map + panel layout).

// =========================================================================
// HOME / DISCOVER
// =========================================================================
function HomeDiscover({ theme, onCluster, onOpenExplorer }) {
  const c = useThemeVars(theme);
  // Pick 4 featured clusters across variety
  const featured = [CLUSTERS[0], CLUSTERS[6], CLUSTERS[4], CLUSTERS[11]];

  return (
    <div>
      <div style={{ padding: '20px 20px 14px' }}>
        <div style={{
          fontFamily: T.mono, fontSize: 10, color: c.muted,
          letterSpacing: 2.2, marginBottom: 6, textTransform: 'uppercase',
        }}>Explore NYC</div>
        <div style={{
          fontSize: 28, fontWeight: 600, color: c.text,
          letterSpacing: -0.8, lineHeight: 1.1, marginBottom: 10,
        }}>Seven thousand<br/>ways to eat.</div>
        <div style={{ fontSize: 13, color: c.muted, lineHeight: 1.5, maxWidth: 320 }}>
          Search by mood, cuisine, or the night you're trying to have. Or browse the
          <span style={{ color: c.text, fontWeight: 500 }}> 50 clusters </span>
          learned from every review in the city.
        </div>
      </div>

      <div style={{
        padding: '10px 20px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div style={{
          fontFamily: T.mono, fontSize: 10, letterSpacing: 2, color: c.muted,
          textTransform: 'uppercase',
        }}>Featured Clusters</div>
        <button
          onClick={onOpenExplorer}
          style={{
            fontFamily: T.mono, fontSize: 10, letterSpacing: 0.5,
            color: c.accent, background: 'transparent', border: 'none', cursor: 'pointer',
            textTransform: 'uppercase',
          }}
        >All 50 →</button>
      </div>

      <div>
        {featured.map(cl => (
          <ClusterCard key={cl.id} cluster={cl} theme={theme}
            onClick={() => onCluster && onCluster(cl)} />
        ))}
      </div>
    </div>
  );
}

// =========================================================================
// SEARCH RESULTS
// =========================================================================
function SearchResults({ query, results, matchedClusters, theme, hoveredId, onHover, onOpen, onBack }) {
  const c = useThemeVars(theme);

  return (
    <div>
      {/* Matched banner */}
      <div style={{
        padding: '12px 20px 14px',
        borderBottom: `1px solid ${c.divider}`,
      }}>
        <div style={{
          fontFamily: T.mono, fontSize: 10, letterSpacing: 2, color: c.muted,
          textTransform: 'uppercase', marginBottom: 6,
        }}>Matched</div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {matchedClusters.map(cl => (
            <div key={cl.id} style={{
              display: 'inline-flex', alignItems: 'center', gap: 5,
              padding: '4px 8px',
              background: c.chip,
              borderRadius: 3,
            }}>
              <span style={{
                fontFamily: T.mono, fontSize: 10, color: c.muted,
                fontVariantNumeric: 'tabular-nums',
              }}>#{String(cl.id).padStart(2, '0')}</span>
              <span style={{
                fontFamily: T.mono, fontSize: 10, color: c.text, letterSpacing: 0.2,
              }}>{cl.keywords.slice(0, 2).join(' · ')}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{
        padding: '10px 20px', display: 'flex', justifyContent: 'space-between',
      }}>
        <div style={{
          fontFamily: T.mono, fontSize: 10, letterSpacing: 2, color: c.muted,
          textTransform: 'uppercase',
        }}>{results.length} places</div>
        <div style={{
          fontFamily: T.mono, fontSize: 10, letterSpacing: 2, color: c.muted,
          textTransform: 'uppercase',
        }}>by similarity</div>
      </div>

      <div style={{ paddingLeft: 24 }}>
        {results.map(r => (
          <ResultCard
            key={r.id}
            restaurant={r}
            theme={theme}
            hovered={hoveredId === r.id}
            onHover={onHover}
            onClick={() => onOpen && onOpen(r)}
            showRank
          />
        ))}
      </div>
    </div>
  );
}

// =========================================================================
// RESTAURANT DETAIL
// =========================================================================
function RestaurantDetail({ restaurant, theme, onBack, onCluster, onOpen }) {
  const c = useThemeVars(theme);
  const cluster = CLUSTERS[restaurant.cluster - 1];
  // Similar = other restaurants in same cluster
  const similar = RESTAURANTS.filter(r => r.cluster === cluster.id && r.id !== restaurant.id).slice(0, 8);
  // If the cluster is small, fall back to nearby
  const filled = similar.length >= 4 ? similar
    : [...similar, ...RESTAURANTS.filter(r => r.borough === restaurant.borough && r.id !== restaurant.id).slice(0, 6)].slice(0, 8);

  return (
    <div style={{
      position: 'absolute', inset: 0,
      background: c.bg,
      overflowY: 'auto',
      zIndex: 30,
    }}>
      {/* Top bar */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 2,
        background: theme === 'dark' ? 'rgba(10,10,10,0.85)' : 'rgba(255,255,255,0.85)',
        backdropFilter: 'blur(18px)', WebkitBackdropFilter: 'blur(18px)',
        borderBottom: `1px solid ${c.divider}`,
        padding: '14px 32px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <button
          onClick={onBack}
          style={{
            fontFamily: T.mono, fontSize: 11, letterSpacing: 0.5,
            color: c.text, background: 'transparent', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 6,
          }}
        >← Back to results</button>
        <div style={{ fontFamily: T.mono, fontSize: 10, color: c.muted, letterSpacing: 2, textTransform: 'uppercase' }}>
          fml /r/{restaurant.id}
        </div>
      </div>

      <div style={{ maxWidth: 960, margin: '0 auto', padding: '48px 32px 80px' }}>
        {/* Hero */}
        <div style={{ marginBottom: 48 }}>
          <div style={{
            fontFamily: T.mono, fontSize: 10, letterSpacing: 2, color: c.accent,
            textTransform: 'uppercase', marginBottom: 14,
          }}>#{String(cluster.id).padStart(2, '0')} · {cluster.keywords[0]}</div>

          <h1 style={{
            fontSize: 56, fontWeight: 600, letterSpacing: -1.6, lineHeight: 1,
            margin: 0, marginBottom: 18, color: c.text,
          }}>{restaurant.name}</h1>

          <div style={{
            display: 'flex', gap: 14, alignItems: 'center',
            fontSize: 15, color: c.muted,
          }}>
            <span style={{ color: c.text }}>{restaurant.neighborhood}</span>
            <span style={{ opacity: 0.4 }}>·</span>
            <span>{restaurant.borough}</span>
            <span style={{ opacity: 0.4 }}>·</span>
            <Rating value={restaurant.rating} theme={theme} size={14} />
            <span style={{ opacity: 0.4 }}>·</span>
            <span style={{ fontFamily: T.mono, fontSize: 13 }}>{restaurant.price}</span>
          </div>
        </div>

        {/* Image placeholder */}
        <div style={{
          height: 320, marginBottom: 64,
          background: `repeating-linear-gradient(45deg, ${c.surface}, ${c.surface} 8px, transparent 8px, transparent 16px)`,
          border: `1px solid ${c.divider}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: T.mono, fontSize: 11, color: c.muted, letterSpacing: 1, textTransform: 'uppercase',
        }}>dining room · exterior · dish</div>

        {/* This place belongs to */}
        <section style={{ marginBottom: 64 }}>
          <SectionLabel theme={theme}>This place belongs to</SectionLabel>
          <div style={{
            padding: '20px 0',
            borderTop: `1px solid ${c.divider}`,
          }}>
            <div
              onClick={() => onCluster && onCluster(cluster)}
              style={{ cursor: 'pointer' }}
            >
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 10 }}>
                <span style={{
                  fontFamily: T.mono, fontSize: 11, color: c.muted, fontVariantNumeric: 'tabular-nums',
                }}>#{String(cluster.id).padStart(2, '0')}</span>
                <span style={{ fontSize: 22, fontWeight: 600, color: c.text, letterSpacing: -0.4 }}>
                  {cluster.keywords.join(' · ')}
                </span>
              </div>
              <div style={{ fontSize: 13, color: c.muted }}>
                {cluster.size} places · mostly {cluster.borough} · avg {cluster.rating.toFixed(1)}★
              </div>
            </div>
          </div>
        </section>

        {/* Reviews */}
        <section style={{ marginBottom: 64 }}>
          <SectionLabel theme={theme}>From the reviews</SectionLabel>
          <div style={{
            columnCount: 2, columnGap: 40, marginTop: 20,
          }}>
            {REVIEWS.slice(0, 5).map((r, i) => (
              <div key={i} style={{
                breakInside: 'avoid', marginBottom: 24,
                paddingLeft: 14, borderLeft: `1px solid ${c.divider}`,
                fontSize: 14, lineHeight: 1.55, color: c.text,
                fontStyle: 'italic',
              }}>
                "{r}"
                <div style={{
                  marginTop: 8, fontSize: 11, fontFamily: T.mono,
                  color: c.muted, fontStyle: 'normal', letterSpacing: 0.3,
                }}>— via Eater, Jan 2026</div>
              </div>
            ))}
          </div>
        </section>

        {/* Similar places */}
        <section>
          <SectionLabel theme={theme}>Similar places</SectionLabel>
          <div style={{
            display: 'flex', gap: 20, overflowX: 'auto', paddingBottom: 20,
            marginTop: 20, scrollbarWidth: 'thin',
          }}>
            {filled.map(r => (
              <div
                key={r.id}
                onClick={() => onOpen && onOpen(r)}
                style={{
                  minWidth: 220, flexShrink: 0, cursor: 'pointer',
                }}
              >
                <div style={{
                  height: 140, marginBottom: 12,
                  background: `repeating-linear-gradient(45deg, ${c.surface}, ${c.surface} 6px, transparent 6px, transparent 12px)`,
                  border: `1px solid ${c.divider}`,
                }} />
                <div style={{ fontSize: 15, fontWeight: 500, color: c.text, marginBottom: 3 }}>{r.name}</div>
                <div style={{ fontSize: 12, color: c.muted, display: 'flex', gap: 6 }}>
                  <span>{r.neighborhood}</span>
                  <span style={{ opacity: 0.4 }}>·</span>
                  <Rating value={r.rating} theme={theme} size={11} />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function SectionLabel({ children, theme }) {
  const c = useThemeVars(theme);
  return (
    <div style={{
      fontFamily: T.mono, fontSize: 10, letterSpacing: 2.4, color: c.muted,
      textTransform: 'uppercase',
    }}>{children}</div>
  );
}

// =========================================================================
// CLUSTER EXPLORER (bottom sheet)
// =========================================================================
function ClusterExplorer({ theme, onClose, onCluster }) {
  const c = useThemeVars(theme);
  return (
    <div style={{
      position: 'absolute', inset: 0, zIndex: 40,
      display: 'flex', flexDirection: 'column', justifyContent: 'flex-end',
      background: theme === 'dark' ? 'rgba(0,0,0,0.4)' : 'rgba(17,24,39,0.15)',
      backdropFilter: 'blur(4px)', WebkitBackdropFilter: 'blur(4px)',
    }}
      onClick={onClose}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          height: '82vh',
          background: c.bg,
          borderTopLeftRadius: 18, borderTopRightRadius: 18,
          borderTop: `1px solid ${c.border}`,
          boxShadow: '0 -16px 60px rgba(0,0,0,0.20)',
          overflow: 'hidden',
          display: 'flex', flexDirection: 'column',
          animation: 'fmlSheetIn 280ms cubic-bezier(.22,.61,.36,1)',
        }}
      >
        {/* Grab handle */}
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 10 }}>
          <div style={{ width: 40, height: 4, borderRadius: 2, background: c.borderStrong }} />
        </div>

        <div style={{ padding: '18px 32px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <div style={{
              fontFamily: T.mono, fontSize: 10, letterSpacing: 2.4, color: c.muted,
              textTransform: 'uppercase', marginBottom: 4,
            }}>50 clusters</div>
            <div style={{ fontSize: 26, fontWeight: 600, color: c.text, letterSpacing: -0.7 }}>
              Every way NYC eats
            </div>
          </div>
          <button onClick={onClose} style={{
            fontFamily: T.mono, fontSize: 11, color: c.muted, background: 'transparent',
            border: 'none', cursor: 'pointer', letterSpacing: 0.5,
          }}>esc ✕</button>
        </div>

        <div style={{
          flex: 1, overflowY: 'auto', padding: '10px 32px 40px',
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))',
            gap: 0,
            borderTop: `1px solid ${c.divider}`,
          }}>
            {CLUSTERS.map(cl => (
              <ClusterGridCard key={cl.id} cluster={cl} theme={theme} onClick={() => onCluster && onCluster(cl)} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ClusterGridCard({ cluster, theme, onClick }) {
  const c = useThemeVars(theme);
  const [hover, setHover] = React.useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        padding: '20px 18px 22px',
        cursor: 'pointer',
        borderRight: `1px solid ${c.divider}`,
        borderBottom: `1px solid ${c.divider}`,
        background: hover ? c.surfaceHover : 'transparent',
        transition: `background ${T.dur}ms ${T.ease}`,
        position: 'relative',
        minHeight: 170,
      }}
    >
      <div style={{
        position: 'absolute', top: 12, right: 14,
        fontFamily: T.mono, fontSize: 10, color: c.muted, fontVariantNumeric: 'tabular-nums',
      }}>#{String(cluster.id).padStart(2, '0')}</div>

      <div style={{ marginBottom: 14, marginTop: 8 }}>
        {cluster.keywords.map((k, i) => (
          <div key={k} style={{
            fontSize: i === 0 ? 19 : (i === 1 ? 15 : 13),
            fontWeight: i === 0 ? 600 : 400,
            color: i === 0 ? c.text : c.muted,
            letterSpacing: -0.3, lineHeight: 1.15,
            opacity: i === 0 ? 1 : (i === 1 ? 0.8 : 0.55),
          }}>{k}</div>
        ))}
      </div>

      <div style={{
        fontFamily: T.mono, fontSize: 10, color: c.muted, letterSpacing: 0.3,
        display: 'flex', gap: 10, alignItems: 'center',
      }}>
        <span style={{ fontVariantNumeric: 'tabular-nums' }}>{cluster.size}</span>
        <span style={{ opacity: 0.4 }}>·</span>
        <Rating value={cluster.rating} theme={theme} size={10} />
        <span style={{ opacity: 0.4 }}>·</span>
        <span>{cluster.borough.toLowerCase()}</span>
      </div>
    </div>
  );
}

// =========================================================================
// COMMAND PALETTE
// =========================================================================
function CommandPalette({ theme, onClose, onSearch, onCluster, onToggleTheme }) {
  const c = useThemeVars(theme);
  const [q, setQ] = React.useState('');
  const [sel, setSel] = React.useState(0);
  const inputRef = React.useRef();

  React.useEffect(() => {
    if (inputRef.current) inputRef.current.focus();
  }, []);

  // Build command list
  const commands = React.useMemo(() => {
    const list = [];
    list.push({ kind: 'action', label: 'Toggle theme', hint: theme === 'dark' ? 'Switch to light' : 'Switch to dark', run: onToggleTheme });
    if (q.trim()) {
      list.push({ kind: 'search', label: `Search for "${q}"`, hint: '↵ to run', run: () => onSearch(q) });
    }
    const qq = q.toLowerCase();
    // Recent / suggested searches
    const suggested = ['cozy italian with outdoor seating', 'quiet date night', 'late-night ramen', 'natural wine and small plates', 'brunch in Brooklyn'];
    for (const s of suggested) {
      if (!q || s.includes(qq)) list.push({ kind: 'suggest', label: s, hint: 'recent', run: () => onSearch(s) });
    }
    // Clusters
    for (const cl of CLUSTERS) {
      const text = cl.keywords.join(' ');
      if (!q || text.includes(qq)) list.push({
        kind: 'cluster', label: cl.keywords.slice(0, 3).join(' · '),
        hint: `#${String(cl.id).padStart(2, '0')} · ${cl.size}`, run: () => onCluster(cl),
      });
    }
    return list.slice(0, 12);
  }, [q, theme]);

  React.useEffect(() => { setSel(0); }, [q]);

  const handleKey = (e) => {
    if (e.key === 'Escape') onClose();
    else if (e.key === 'ArrowDown') { e.preventDefault(); setSel(s => Math.min(commands.length - 1, s + 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setSel(s => Math.max(0, s - 1)); }
    else if (e.key === 'Enter') { e.preventDefault(); commands[sel]?.run(); onClose(); }
  };

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 80,
        background: theme === 'dark' ? 'rgba(0,0,0,0.5)' : 'rgba(17,24,39,0.25)',
        backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)',
        display: 'flex', justifyContent: 'center', paddingTop: '14vh',
        animation: 'fmlFadeIn 160ms ease-out',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: 640, maxWidth: '94vw',
          background: c.bg,
          border: `1px solid ${c.border}`,
          borderRadius: 12,
          boxShadow: '0 24px 80px rgba(0,0,0,0.35), 0 1px 0 rgba(255,255,255,0.04) inset',
          overflow: 'hidden',
          animation: 'fmlCmdkIn 200ms cubic-bezier(.22,.61,.36,1)',
        }}
      >
        <div style={{ padding: '14px 18px', borderBottom: `1px solid ${c.divider}`, display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontFamily: T.mono, fontSize: 11, color: c.muted, letterSpacing: 0.5 }}>⌘K</span>
          <input
            ref={inputRef}
            value={q}
            onChange={e => setQ(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Type a command, cluster, or search…"
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              fontFamily: T.font, fontSize: 16, color: c.text,
            }}
          />
        </div>
        <div style={{ maxHeight: 380, overflowY: 'auto', padding: '6px 0' }}>
          {commands.map((cmd, i) => (
            <div
              key={i}
              onMouseEnter={() => setSel(i)}
              onClick={() => { cmd.run(); onClose(); }}
              style={{
                padding: '10px 18px',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                background: sel === i ? c.surfaceHover : 'transparent',
                cursor: 'pointer',
                borderLeft: sel === i ? `2px solid ${c.accent}` : '2px solid transparent',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{
                  fontFamily: T.mono, fontSize: 9, color: c.muted, letterSpacing: 1.5,
                  textTransform: 'uppercase', width: 54, display: 'inline-block',
                }}>{cmd.kind}</span>
                <span style={{ fontSize: 14, color: c.text }}>{cmd.label}</span>
              </div>
              <span style={{ fontFamily: T.mono, fontSize: 10.5, color: c.muted, letterSpacing: 0.3 }}>{cmd.hint}</span>
            </div>
          ))}
          {commands.length === 0 && (
            <div style={{ padding: '30px 18px', textAlign: 'center', color: c.muted, fontSize: 13 }}>
              Nothing matches "{q}"
            </div>
          )}
        </div>
        <div style={{ padding: '10px 18px', borderTop: `1px solid ${c.divider}`, display: 'flex', gap: 18, fontFamily: T.mono, fontSize: 10, color: c.muted, letterSpacing: 0.4 }}>
          <span>↑↓ navigate</span>
          <span>↵ select</span>
          <span>esc close</span>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { HomeDiscover, SearchResults, RestaurantDetail, ClusterExplorer, CommandPalette });

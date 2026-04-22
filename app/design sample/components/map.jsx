// map.jsx — stylized NYC map in SVG. Boroughs, rivers, subtle grid, dots.

// Abstract borough silhouettes — not topologically correct, but legible as NYC.
// Coordinates in a 1000x800 viewbox.
const BOROUGH_PATHS = {
  // Manhattan — vertical finger
  manhattan: 'M 452 230 L 470 225 L 490 240 L 504 270 L 510 310 L 506 360 L 504 420 L 500 470 L 494 520 L 488 570 L 478 610 L 462 622 L 448 605 L 440 560 L 438 510 L 440 460 L 442 410 L 446 360 L 448 310 L 450 270 Z',
  // Bronx — above Manhattan, broad
  bronx: 'M 440 180 L 478 172 L 520 170 L 560 174 L 590 186 L 604 210 L 600 240 L 584 262 L 560 268 L 530 272 L 498 268 L 472 252 L 452 232 L 438 210 Z',
  // Brooklyn — south-east sprawl
  brooklyn: 'M 510 440 L 548 438 L 590 442 L 632 452 L 664 468 L 682 492 L 688 522 L 684 556 L 672 590 L 648 618 L 612 638 L 572 650 L 536 646 L 512 624 L 502 592 L 498 560 L 500 524 L 502 488 L 506 460 Z',
  // Queens — east, wide
  queens: 'M 614 300 L 660 292 L 708 294 L 756 300 L 796 312 L 820 336 L 828 362 L 822 394 L 808 424 L 782 452 L 744 474 L 702 484 L 662 482 L 628 470 L 612 448 L 608 416 L 612 380 L 614 342 Z',
  // Staten Island — isolated blob, lower-left
  si: 'M 350 608 L 384 602 L 416 608 L 432 628 L 434 656 L 424 686 L 400 706 L 372 710 L 348 698 L 336 674 L 336 644 L 340 620 Z',
};

// River polygons (the water between boroughs)
// East River + Hudson + Harlem as broad strokes
const WATER_PATHS = [
  // Hudson (west of Manhattan)
  'M 340 160 L 430 180 L 436 280 L 440 380 L 442 480 L 448 580 L 456 650 L 460 720 L 330 730 L 320 600 L 325 420 L 335 260 Z',
  // East River between Manhattan and Brooklyn/Queens
  'M 504 260 L 540 250 L 610 270 L 612 340 L 610 400 L 608 460 L 590 472 L 564 478 L 540 482 L 514 484 L 506 460 L 504 410 L 502 360 L 502 310 Z',
  // Newtown Creek / gap between Brooklyn & Queens
  'M 602 440 L 640 438 L 668 446 L 664 470 L 636 472 L 610 464 Z',
  // Harlem River
  'M 438 230 L 478 238 L 500 252 L 506 268 L 486 272 L 460 264 L 438 252 Z',
  // NY Bay below
  'M 330 620 L 470 630 L 500 660 L 510 700 L 490 740 L 400 748 L 310 740 L 290 700 L 300 660 Z',
];

function NYCMap({
  dots, restaurants, highlightedIds, dimmed, theme, onMarkerHover, onMarkerClick, hoveredId,
}) {
  const isDark = theme === 'dark';
  const land = isDark ? '#141414' : '#F5F4F0';
  const landStroke = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(17,24,39,0.08)';
  const water = isDark ? '#0A0A0A' : '#E8EEF2';
  const grid = isDark ? 'rgba(255,255,255,0.025)' : 'rgba(17,24,39,0.04)';
  const parkFill = isDark ? 'rgba(80,120,80,0.10)' : 'rgba(80,140,80,0.08)';

  // Single accent — indigo
  const accent = '#1E3A8A';
  const accentMarker = isDark ? '#818CF8' : '#1E3A8A';

  return (
    <svg
      viewBox="0 0 1000 800"
      preserveAspectRatio="xMidYMid slice"
      style={{ width: '100%', height: '100%', display: 'block' }}
    >
      {/* Water base */}
      <rect width="1000" height="800" fill={water} />

      {/* Micro grid */}
      <defs>
        <pattern id="fml-grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke={grid} strokeWidth="0.5" />
        </pattern>
        <pattern id="fml-grid-fine" width="8" height="8" patternUnits="userSpaceOnUse">
          <path d="M 8 0 L 0 0 0 8" fill="none" stroke={grid} strokeWidth="0.25" />
        </pattern>
        <radialGradient id="fml-glow">
          <stop offset="0%" stopColor={accentMarker} stopOpacity="0.35" />
          <stop offset="100%" stopColor={accentMarker} stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="1000" height="800" fill="url(#fml-grid)" />

      {/* Land masses */}
      <g>
        {Object.entries(BOROUGH_PATHS).map(([name, d]) => (
          <path key={name} d={d} fill={land} stroke={landStroke} strokeWidth="1" />
        ))}
      </g>
      {/* Fine grid on land only — trick with clip path would be ideal; keep it simple */}
      <g opacity={isDark ? 0.3 : 0.5}>
        {Object.entries(BOROUGH_PATHS).map(([name, d]) => (
          <path key={name + '-clip'} d={d} fill="url(#fml-grid-fine)" />
        ))}
      </g>

      {/* Central Park */}
      <rect x="464" y="370" width="22" height="55" fill={parkFill} rx="1" />
      {/* Prospect Park */}
      <path d="M 556 532 L 582 528 L 588 552 L 572 572 L 552 566 Z" fill={parkFill} />

      {/* Dots — thousands of restaurants */}
      <g>
        {dots.map((d, i) => {
          const hue = CLUSTERS[d.c - 1]?.hue || 220;
          const color = isDark
            ? `hsla(${hue}, 45%, 72%, ${dimmed ? 0.06 : 0.28})`
            : `hsla(${hue}, 55%, 38%, ${dimmed ? 0.05 : 0.22})`;
          return <circle key={i} cx={d.x} cy={d.y} r={0.9} fill={color} />;
        })}
      </g>

      {/* Result markers */}
      {restaurants && restaurants.map((r, i) => {
        const isHovered = hoveredId === r.id;
        const size = Math.max(5, 14 - i * 0.6) + (isHovered ? 4 : 0);
        return (
          <g
            key={r.id}
            style={{ cursor: 'pointer', transition: 'transform 160ms ease-out' }}
            onMouseEnter={() => onMarkerHover && onMarkerHover(r.id)}
            onMouseLeave={() => onMarkerHover && onMarkerHover(null)}
            onClick={() => onMarkerClick && onMarkerClick(r.id)}
          >
            {isHovered && <circle cx={r.x} cy={r.y} r={size + 18} fill="url(#fml-glow)" />}
            <circle cx={r.x} cy={r.y} r={size + 2} fill={isDark ? '#0A0A0A' : '#FFFFFF'} />
            <circle cx={r.x} cy={r.y} r={size} fill={accentMarker} />
            <text
              x={r.x} y={r.y + 2.6}
              fontFamily="ui-monospace, SF Mono, Menlo, monospace"
              fontSize={size * 0.75}
              fontWeight="600"
              fill={isDark ? '#0A0A0A' : '#FFFFFF'}
              textAnchor="middle"
              style={{ pointerEvents: 'none', fontVariantNumeric: 'tabular-nums' }}
            >{r.rank || i + 1}</text>
          </g>
        );
      })}

      {/* Highlighted (non-result) point */}
      {highlightedIds && highlightedIds.map(id => {
        const r = RESTAURANTS.find(x => x.id === id);
        if (!r) return null;
        return <circle key={'h'+id} cx={r.x} cy={r.y} r={5} fill={accentMarker} stroke={isDark ? '#0A0A0A' : '#FFFFFF'} strokeWidth="2" />;
      })}

      {/* Borough labels — quiet serif-ish caps */}
      <g style={{ pointerEvents: 'none' }}>
        {[
          { name: 'MANHATTAN', x: 470, y: 400 },
          { name: 'BROOKLYN', x: 595, y: 545 },
          { name: 'QUEENS', x: 720, y: 390 },
          { name: 'BRONX', x: 520, y: 220 },
          { name: 'STATEN ISLAND', x: 385, y: 660 },
        ].map(l => (
          <text
            key={l.name}
            x={l.x} y={l.y}
            fontFamily='-apple-system, BlinkMacSystemFont, "SF Pro Display", Inter, sans-serif'
            fontSize="10"
            fontWeight="500"
            letterSpacing="2.5"
            fill={isDark ? 'rgba(250,250,250,0.30)' : 'rgba(17,24,39,0.38)'}
            textAnchor="middle"
          >{l.name}</text>
        ))}
      </g>
    </svg>
  );
}

Object.assign(window, { NYCMap });

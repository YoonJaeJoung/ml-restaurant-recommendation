// data.jsx — plausible NYC restaurant + cluster fixtures for FML

// 50 clusters: semantic groupings learned from review embeddings (faked).
// Each has top_keywords, a size, an avg rating, a top borough, and a hue
// used purely for the tiny dots on the map.
const CLUSTERS = [
  { id: 1,  keywords: ['date-night', 'dim-lit', 'natural-wine'], size: 412, rating: 4.5, borough: 'Manhattan', hue: 238 },
  { id: 2,  keywords: ['old-school', 'red-sauce', 'italian'], size: 287, rating: 4.3, borough: 'Manhattan', hue: 12 },
  { id: 3,  keywords: ['outdoor', 'sidewalk', 'brunch'], size: 521, rating: 4.1, borough: 'Brooklyn', hue: 84 },
  { id: 4,  keywords: ['ramen', 'counter', 'slurp'], size: 189, rating: 4.4, borough: 'Manhattan', hue: 20 },
  { id: 5,  keywords: ['dumplings', 'handmade', 'family'], size: 234, rating: 4.5, borough: 'Queens', hue: 340 },
  { id: 6,  keywords: ['tasting-menu', 'quiet', 'refined'], size: 67, rating: 4.7, borough: 'Manhattan', hue: 260 },
  { id: 7,  keywords: ['italian-casual', 'pasta', 'neighborhood'], size: 356, rating: 4.3, borough: 'Brooklyn', hue: 4 },
  { id: 8,  keywords: ['natural-wine', 'small-plates', 'cool'], size: 178, rating: 4.2, borough: 'Brooklyn', hue: 300 },
  { id: 9,  keywords: ['dive-bar', 'late-night', 'cheap'], size: 445, rating: 3.9, borough: 'Manhattan', hue: 40 },
  { id: 10, keywords: ['sushi', 'omakase', 'counter'], size: 98, rating: 4.6, borough: 'Manhattan', hue: 200 },
  { id: 11, keywords: ['pizza', 'slice', 'grab-and-go'], size: 612, rating: 4.0, borough: 'Brooklyn', hue: 15 },
  { id: 12, keywords: ['date-night', 'rooftop', 'cocktails'], size: 143, rating: 4.4, borough: 'Manhattan', hue: 252 },
  { id: 13, keywords: ['vegetarian', 'seasonal', 'bright'], size: 221, rating: 4.3, borough: 'Brooklyn', hue: 120 },
  { id: 14, keywords: ['taqueria', 'al-pastor', 'neighborhood'], size: 389, rating: 4.2, borough: 'Queens', hue: 30 },
  { id: 15, keywords: ['steakhouse', 'classic', 'power-lunch'], size: 89, rating: 4.3, borough: 'Manhattan', hue: 0 },
  { id: 16, keywords: ['korean-bbq', 'smoky', 'group'], size: 156, rating: 4.4, borough: 'Manhattan', hue: 350 },
  { id: 17, keywords: ['french', 'bistro', 'classic'], size: 134, rating: 4.4, borough: 'Manhattan', hue: 220 },
  { id: 18, keywords: ['chinese', 'banquet', 'family-style'], size: 267, rating: 4.2, borough: 'Queens', hue: 355 },
  { id: 19, keywords: ['bakery', 'pastry', 'morning'], size: 298, rating: 4.3, borough: 'Manhattan', hue: 35 },
  { id: 20, keywords: ['coffee', 'laptop-friendly', 'all-day'], size: 534, rating: 4.1, borough: 'Brooklyn', hue: 25 },
  { id: 21, keywords: ['hidden-gem', 'tiny', 'chef-driven'], size: 112, rating: 4.6, borough: 'Brooklyn', hue: 270 },
  { id: 22, keywords: ['late-night', 'after-hours', 'energy'], size: 198, rating: 4.0, borough: 'Manhattan', hue: 290 },
  { id: 23, keywords: ['seafood', 'raw-bar', 'oysters'], size: 124, rating: 4.3, borough: 'Manhattan', hue: 180 },
  { id: 24, keywords: ['thai', 'spicy', 'bold'], size: 178, rating: 4.3, borough: 'Queens', hue: 50 },
  { id: 25, keywords: ['vietnamese', 'pho', 'broth'], size: 156, rating: 4.2, borough: 'Brooklyn', hue: 70 },
  { id: 26, keywords: ['indian', 'spice', 'regional'], size: 201, rating: 4.2, borough: 'Queens', hue: 45 },
  { id: 27, keywords: ['middle-eastern', 'mezze', 'hummus'], size: 167, rating: 4.3, borough: 'Brooklyn', hue: 60 },
  { id: 28, keywords: ['cafe', 'brunch', 'scene'], size: 312, rating: 4.0, borough: 'Manhattan', hue: 28 },
  { id: 29, keywords: ['wine-bar', 'snacks', 'low-key'], size: 189, rating: 4.3, borough: 'Brooklyn', hue: 330 },
  { id: 30, keywords: ['bbq', 'smoke', 'meats'], size: 78, rating: 4.2, borough: 'Brooklyn', hue: 18 },
  { id: 31, keywords: ['burger', 'classic', 'juicy'], size: 234, rating: 4.1, borough: 'Manhattan', hue: 22 },
  { id: 32, keywords: ['japanese', 'izakaya', 'sake'], size: 112, rating: 4.4, borough: 'Manhattan', hue: 215 },
  { id: 33, keywords: ['caribbean', 'jerk', 'island'], size: 145, rating: 4.2, borough: 'Brooklyn', hue: 140 },
  { id: 34, keywords: ['ethiopian', 'injera', 'shared'], size: 56, rating: 4.4, borough: 'Bronx', hue: 10 },
  { id: 35, keywords: ['soul-food', 'comfort', 'classics'], size: 89, rating: 4.3, borough: 'Bronx', hue: 38 },
  { id: 36, keywords: ['brewery', 'beer-hall', 'long-tables'], size: 67, rating: 4.1, borough: 'Brooklyn', hue: 48 },
  { id: 37, keywords: ['speakeasy', 'cocktails', 'dark'], size: 134, rating: 4.3, borough: 'Manhattan', hue: 255 },
  { id: 38, keywords: ['jewish-deli', 'pastrami', 'iconic'], size: 34, rating: 4.4, borough: 'Manhattan', hue: 8 },
  { id: 39, keywords: ['dumpling', 'xiao-long-bao', 'soup'], size: 89, rating: 4.5, borough: 'Queens', hue: 345 },
  { id: 40, keywords: ['mediterranean', 'grill', 'airy'], size: 145, rating: 4.2, borough: 'Manhattan', hue: 195 },
  { id: 41, keywords: ['peruvian', 'ceviche', 'fresh'], size: 78, rating: 4.3, borough: 'Queens', hue: 160 },
  { id: 42, keywords: ['spanish', 'tapas', 'jamon'], size: 89, rating: 4.3, borough: 'Manhattan', hue: 25 },
  { id: 43, keywords: ['greek', 'seafood', 'white-walls'], size: 67, rating: 4.4, borough: 'Queens', hue: 205 },
  { id: 44, keywords: ['farm-to-table', 'market', 'quiet'], size: 56, rating: 4.5, borough: 'Brooklyn', hue: 100 },
  { id: 45, keywords: ['tea-house', 'matcha', 'pastry'], size: 123, rating: 4.2, borough: 'Manhattan', hue: 130 },
  { id: 46, keywords: ['cozy', 'fireplace', 'winter'], size: 45, rating: 4.5, borough: 'Brooklyn', hue: 15 },
  { id: 47, keywords: ['scandinavian', 'minimal', 'precise'], size: 23, rating: 4.6, borough: 'Manhattan', hue: 210 },
  { id: 48, keywords: ['hotel-bar', 'lobby', 'quiet-luxury'], size: 56, rating: 4.2, borough: 'Manhattan', hue: 240 },
  { id: 49, keywords: ['food-hall', 'busy', 'variety'], size: 34, rating: 4.0, borough: 'Manhattan', hue: 50 },
  { id: 50, keywords: ['waterfront', 'view', 'sunset'], size: 45, rating: 4.2, borough: 'Brooklyn', hue: 185 },
];

// 50 curated restaurants with plausible-but-invented names. Each has a
// cluster, a neighborhood, a rating, and coordinates in our stylized
// map space (0-1000 x 0-800).
const RESTAURANTS = [
  { id: 1,  name: 'Osteria Poline', neighborhood: 'West Village', borough: 'Manhattan', cluster: 2, rating: 4.5, price: '$$$', x: 482, y: 482 },
  { id: 2,  name: 'Casa Ferrara', neighborhood: 'Greenpoint', borough: 'Brooklyn', cluster: 7, rating: 4.6, price: '$$$', x: 602, y: 438 },
  { id: 3,  name: 'The Muted Room', neighborhood: 'Tribeca', borough: 'Manhattan', cluster: 6, rating: 4.8, price: '$$$$', x: 476, y: 512 },
  { id: 4,  name: 'Hōrin', neighborhood: 'East Village', borough: 'Manhattan', cluster: 10, rating: 4.7, price: '$$$$', x: 512, y: 472 },
  { id: 5,  name: 'Le Pigeon Bleu', neighborhood: 'Chelsea', borough: 'Manhattan', cluster: 17, rating: 4.4, price: '$$$', x: 472, y: 442 },
  { id: 6,  name: 'Saltwick', neighborhood: 'Williamsburg', borough: 'Brooklyn', cluster: 8, rating: 4.3, price: '$$', x: 588, y: 462 },
  { id: 7,  name: 'Menta', neighborhood: 'Cobble Hill', borough: 'Brooklyn', cluster: 13, rating: 4.4, price: '$$', x: 542, y: 552 },
  { id: 8,  name: 'Don Cantina', neighborhood: 'Jackson Heights', borough: 'Queens', cluster: 14, rating: 4.5, price: '$', x: 722, y: 412 },
  { id: 9,  name: 'Linden Park', neighborhood: 'Fort Greene', borough: 'Brooklyn', cluster: 1, rating: 4.5, price: '$$$', x: 582, y: 522 },
  { id: 10, name: 'Fosca', neighborhood: 'Nolita', borough: 'Manhattan', cluster: 1, rating: 4.4, price: '$$$', x: 502, y: 492 },
  { id: 11, name: 'Nineteen Ten', neighborhood: 'Upper East Side', borough: 'Manhattan', cluster: 15, rating: 4.3, price: '$$$$', x: 498, y: 362 },
  { id: 12, name: 'Shiso & Sea', neighborhood: 'Nomad', borough: 'Manhattan', cluster: 23, rating: 4.3, price: '$$$', x: 488, y: 412 },
  { id: 13, name: 'Bushwick Deli Club', neighborhood: 'Bushwick', borough: 'Brooklyn', cluster: 9, rating: 4.0, price: '$', x: 648, y: 498 },
  { id: 14, name: 'Ardo', neighborhood: 'Carroll Gardens', borough: 'Brooklyn', cluster: 21, rating: 4.7, price: '$$$', x: 548, y: 568 },
  { id: 15, name: 'Piccola Luna', neighborhood: 'Park Slope', borough: 'Brooklyn', cluster: 7, rating: 4.4, price: '$$', x: 572, y: 578 },
  { id: 16, name: 'Torch House', neighborhood: 'Koreatown', borough: 'Manhattan', cluster: 16, rating: 4.5, price: '$$$', x: 482, y: 422 },
  { id: 17, name: 'Bāzi', neighborhood: 'Astoria', borough: 'Queens', cluster: 26, rating: 4.4, price: '$$', x: 682, y: 382 },
  { id: 18, name: 'Kew Pho House', neighborhood: 'Elmhurst', borough: 'Queens', cluster: 25, rating: 4.3, price: '$', x: 738, y: 428 },
  { id: 19, name: 'Sunflower Grain', neighborhood: 'Gowanus', borough: 'Brooklyn', cluster: 13, rating: 4.2, price: '$$', x: 572, y: 558 },
  { id: 20, name: 'Oyster Row', neighborhood: 'West Village', borough: 'Manhattan', cluster: 23, rating: 4.4, price: '$$$', x: 478, y: 478 },
  { id: 21, name: 'Little Aegean', neighborhood: 'Astoria', borough: 'Queens', cluster: 43, rating: 4.5, price: '$$', x: 692, y: 388 },
  { id: 22, name: 'Copperleaf', neighborhood: 'Prospect Heights', borough: 'Brooklyn', cluster: 44, rating: 4.6, price: '$$$', x: 598, y: 552 },
  { id: 23, name: 'The Quiet Bar', neighborhood: 'Lower East Side', borough: 'Manhattan', cluster: 37, rating: 4.3, price: '$$', x: 518, y: 502 },
  { id: 24, name: 'North Harbor', neighborhood: 'Red Hook', borough: 'Brooklyn', cluster: 50, rating: 4.3, price: '$$$', x: 538, y: 588 },
  { id: 25, name: 'Wren & Barrow', neighborhood: 'Boerum Hill', borough: 'Brooklyn', cluster: 29, rating: 4.2, price: '$$', x: 552, y: 542 },
];

// Review snippets for the detail page
const REVIEWS = [
  'The room hums at just the right volume — you can actually have a conversation.',
  'House-made pasta, but they aren\'t precious about it.',
  'Came for the pasta, stayed for the Barolo list.',
  'That warm focaccia arrives before you\'ve even sat down.',
  'Tiny dining room, maybe eighteen seats. Book ahead.',
  'The olive oil alone is worth the trip.',
];

// Semantic "matches" — a query maps to a handful of clusters with weights
function semanticMatch(query) {
  const q = query.toLowerCase();
  const matches = [];
  for (const c of CLUSTERS) {
    let score = 0;
    for (const k of c.keywords) {
      if (q.includes(k.replace('-', ' ')) || q.includes(k)) score += 1;
      const parts = k.split('-');
      for (const p of parts) if (p.length > 3 && q.includes(p)) score += 0.5;
    }
    // vibe synonyms
    const synonyms = {
      'cozy': [1, 46, 21], 'romantic': [1, 12, 6], 'quiet': [6, 44, 47],
      'loud': [22, 9, 49], 'cheap': [9, 11, 14], 'fancy': [6, 10, 15, 47],
      'italian': [2, 7], 'japanese': [4, 10, 32], 'mexican': [14],
      'outdoor': [3, 12, 50], 'date': [1, 6, 12], 'brunch': [3, 28],
      'wine': [1, 8, 29, 42], 'cocktail': [12, 37],
      'late': [9, 22, 37], 'vegetarian': [13, 44],
      'dumpling': [5, 39], 'pasta': [2, 7], 'pizza': [11],
      'sushi': [10], 'ramen': [4], 'seafood': [23, 43, 50],
      'view': [12, 50], 'tasting': [6, 47],
    };
    for (const [syn, ids] of Object.entries(synonyms)) {
      if (q.includes(syn) && ids.includes(c.id)) score += 1.2;
    }
    if (score > 0) matches.push({ cluster: c, score });
  }
  matches.sort((a, b) => b.score - a.score);
  return matches.slice(0, 4);
}

// Find 10 restaurants for a query, ranked
function searchRestaurants(query) {
  const matches = semanticMatch(query);
  if (matches.length === 0) return { restaurants: [], clusters: [] };
  const clusterIds = matches.map(m => m.cluster.id);
  const scored = RESTAURANTS.map(r => {
    const idx = clusterIds.indexOf(r.cluster);
    const baseScore = idx >= 0 ? (matches.length - idx) * 20 : 0;
    const jitter = (r.id * 13) % 17; // deterministic jitter
    return { r, score: baseScore + jitter + r.rating * 5 };
  }).sort((a, b) => b.score - a.score);
  const top = scored.slice(0, 10);
  const maxS = top[0]?.score || 1;
  return {
    restaurants: top.map((s, i) => ({
      ...s.r,
      similarity: Math.max(0.55, s.score / maxS),
      rank: i + 1,
    })),
    clusters: matches.slice(0, 3).map(m => m.cluster),
  };
}

// Generate ~21k dots across the map space, weighted by cluster location
function generateDotField(seed = 1) {
  // Deterministic PRNG
  let s = seed;
  const rnd = () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
  const dots = [];
  // Manhattan strip
  const manhattan = { x0: 440, y0: 260, x1: 520, y1: 620 };
  // Brooklyn
  const brooklyn = { x0: 520, y0: 440, x1: 680, y1: 660 };
  // Queens
  const queens = { x0: 620, y0: 300, x1: 820, y1: 500 };
  // Bronx
  const bronx = { x0: 460, y0: 180, x1: 600, y1: 280 };
  // Staten Island
  const si = { x0: 340, y0: 600, x1: 440, y1: 720 };
  const zones = [
    { z: manhattan, w: 7500 }, { z: brooklyn, w: 6500 },
    { z: queens, w: 4500 }, { z: bronx, w: 1800 }, { z: si, w: 700 },
  ];
  for (const { z, w } of zones) {
    for (let i = 0; i < w; i++) {
      dots.push({
        x: z.x0 + rnd() * (z.x1 - z.x0),
        y: z.y0 + rnd() * (z.y1 - z.y0),
        c: Math.floor(rnd() * 50) + 1, // cluster id
      });
    }
  }
  return dots;
}

const DOTS = generateDotField(7);

Object.assign(window, { CLUSTERS, RESTAURANTS, REVIEWS, semanticMatch, searchRestaurants, generateDotField, DOTS });

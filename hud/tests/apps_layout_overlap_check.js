'use strict';
/**
 * Headless: layoutApps vs real HUD occupied rects → zero AABB overlap.
 *
 * Fixture source:
 *   - Occupied widget rects = hud/layout_check.json (7 existing HUD elements).
 *   - h1_gui_result.json (2026-10-09 03:36 CDP session) recorded overlap *names*
 *     ("stats draggable x jarvis-app-card") but not full rect payloads; the same
 *     session's baseline rects live in layout_check.json (cited in the bug report).
 *   - Card size = hw-ring app.json [220, 160].
 *   - Bounds 2560×1440 inferred from those rects (panel-right right edge ~2457).
 *
 * Run: node hud/tests/apps_layout_overlap_check.js
 */
const assert = require('assert');
const reg = require('../apps_registry');

// Rounded from hud/layout_check.json (source note above).
const OCCUPIED = [
  { c: 'stats', x: 102, y: 1080, w: 320, h: 245 },
  { c: 'levels', x: 2138, y: 918, w: 320, h: 263 },
  { c: 'weather', x: 1178, y: 180, w: 205, h: 119 },
  { c: 'greeting', x: 1132, y: 302, w: 296, h: 48 },
  { c: 'clockblock', x: 102, y: 101, w: 323, h: 117 },
  { c: 'panel.left', x: 102, y: 274, w: 333, h: 723 },
  { c: 'panel.right', x: 2125, y: 274, w: 333, h: 462 },
];

const BOUNDS = { width: 2560, height: 1440 };
const HW_RING = { id: 'hw-ring', size: [220, 160], name: '負載環', icon: '◎' };

function cardRect(p) {
  return { x: p.x, y: p.y, w: p.w, h: p.h };
}

function assertClearOfOccupied(placed, mode) {
  for (const p of placed) {
    const cr = cardRect(p);
    for (const o of OCCUPIED) {
      assert.ok(
        !reg.rectsOverlap(cr, o),
        mode + ': ' + p.id + ' overlaps ' + o.c + ' card=' + JSON.stringify(cr) + ' occ=' + JSON.stringify(o)
      );
    }
  }
  for (let i = 0; i < placed.length; i++) {
    for (let j = i + 1; j < placed.length; j++) {
      assert.ok(
        !reg.rectsOverlap(cardRect(placed[i]), cardRect(placed[j])),
        mode + ': cards overlap ' + placed[i].id + ' x ' + placed[j].id
      );
    }
  }
}

const logs = [];
const carousel = reg.layoutApps(
  [HW_RING],
  'carousel',
  BOUNDS,
  (m) => logs.push(m),
  OCCUPIED
);
assert.strictEqual(carousel.length, 1);
assertClearOfOccupied(carousel, 'carousel');
console.log('PASS carousel vs occupied: ' + JSON.stringify(cardRect(carousel[0])));
console.log('  resolve logs: ' + (logs.filter((l) => /overlap resolve/.test(l)).length));

const freeLogs = [];
const free = reg.layoutApps(
  [{ id: 'hw-ring', size: [220, 160], x: 40, y: BOUNDS.height - 200 }],
  'free',
  BOUNDS,
  (m) => freeLogs.push(m),
  OCCUPIED
);
assert.strictEqual(free.length, 1);
assertClearOfOccupied(free, 'free');
console.log('PASS free vs occupied: ' + JSON.stringify(cardRect(free[0])));
console.log('  resolve logs: ' + (freeLogs.filter((l) => /overlap resolve/.test(l)).length));

// Sanity: without occupied, carousel still lands on the old band (would overlap stats).
const naive = reg.layoutApps([HW_RING], 'carousel', BOUNDS, () => {}, []);
assert.ok(
  OCCUPIED.some((o) => reg.rectsOverlap(cardRect(naive[0]), o)),
  'fixture sanity: naive carousel must hit occupied (else fixture wrong)'
);
console.log('PASS fixture sanity: naive carousel hits occupied at ' + JSON.stringify(cardRect(naive[0])));

console.log('\nALL PASS');
process.exit(0);

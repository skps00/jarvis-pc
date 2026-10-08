'use strict';
/**
 * Headless unit checks for hud/apps_registry.js (HoloMat H1).
 * Run: node hud/tests/apps_registry_check.js
 */
const fs = require('fs');
const path = require('path');
const os = require('os');
const assert = require('assert');

const reg = require('../apps_registry');

const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'jarvis-apps-reg-'));
const appsDir = path.join(tmpRoot, 'apps');
const jarvisDir = path.join(tmpRoot, 'Jarvis');
fs.mkdirSync(appsDir, { recursive: true });
fs.mkdirSync(jarvisDir, { recursive: true });

const logs = [];
function logFn(m) { logs.push(String(m)); }

function writeApp(folder, json, js) {
  const d = path.join(appsDir, folder);
  fs.mkdirSync(d, { recursive: true });
  if (json != null) fs.writeFileSync(path.join(d, 'app.json'), json, 'utf8');
  if (js != null) fs.writeFileSync(path.join(d, 'app.js'), js, 'utf8');
}

let failed = 0;
function check(name, fn) {
  try {
    fn();
    console.log('PASS ' + name);
  } catch (e) {
    failed += 1;
    console.log('FAIL ' + name + ': ' + (e && e.stack ? e.stack : e));
  }
}

// ① normal app.json
check('load normal app.json', () => {
  writeApp('good', JSON.stringify({
    id: 'good', name: 'Good', api: ['sensors'], size: [200, 100], x: 10, y: 10,
  }), 'function register(J){}');
  const mans = reg.loadAppManifests(appsDir, logFn);
  assert.ok(mans.some((m) => m.id === 'good'), 'good app missing');
});

// ② bad JSON → skip, no throw
check('bad JSON skipped, no throw', () => {
  writeApp('badjson', '{not json', null);
  let threw = false;
  let mans;
  try {
    mans = reg.loadAppManifests(appsDir, logFn);
  } catch (e) {
    threw = true;
  }
  assert.strictEqual(threw, false, 'must not throw');
  assert.ok(!mans.some((m) => m.id === 'badjson'));
  assert.ok(logs.some((l) => /bad JSON/i.test(l)), 'expected bad JSON log');
});

// ③ missing id → skip
check('missing id skipped', () => {
  writeApp('noid', JSON.stringify({ name: 'NoId', api: [] }), null);
  const mans = reg.loadAppManifests(appsDir, logFn);
  assert.ok(!mans.some((m) => m.name === 'NoId' && !m.id));
  assert.ok(!mans.some((m) => path.basename(m.dir) === 'noid'));
});

// ④ empty dir → 0 apps
check('empty dir → 0', () => {
  const empty = path.join(tmpRoot, 'empty');
  fs.mkdirSync(empty, { recursive: true });
  const mans = reg.loadAppManifests(empty, logFn);
  assert.strictEqual(mans.length, 0);
});

// ⑤ free layout overlap → nudge + log
check('free layout overlap resolves', () => {
  const mans = [
    { id: 'a', size: [100, 80], x: 0, y: 0 },
    { id: 'b', size: [100, 80], x: 10, y: 10 }, // overlaps a
  ];
  const layLogs = [];
  const placed = reg.layoutApps(mans, 'free', { width: 800, height: 600 }, (m) => layLogs.push(m));
  assert.strictEqual(placed.length, 2);
  assert.ok(placed[0].x === 0 && placed[0].y === 0);
  assert.ok(placed[1].x !== 10 || placed[1].y !== 10, 'b coords must change');
  assert.ok(!reg.rectsOverlap(
    { x: placed[0].x, y: placed[0].y, w: placed[0].w, h: placed[0].h },
    { x: placed[1].x, y: placed[1].y, w: placed[1].w, h: placed[1].h }
  ), 'still overlapping');
  assert.ok(layLogs.some((l) => /overlap resolve/.test(l)), 'expected overlap log');
});

// ⑥ whitelist: undeclared api blocked
check('api whitelist gate', () => {
  assert.strictEqual(reg.isApiAllowed(['sensors'], 'sensors'), true);
  assert.strictEqual(reg.isApiAllowed(['sensors'], 'speak'), false);
  assert.strictEqual(reg.isApiAllowed(['sensors'], 'register'), true);
  assert.strictEqual(reg.isApiAllowed([], 'fs'), false);
  assert.strictEqual(reg.isApiAllowed(['log'], 'child_process'), false);
});

// 負控：壞 app.json 唔拖死其他 app
check('negative: bad json does not skip siblings', () => {
  writeApp('sibling', JSON.stringify({
    id: 'sibling', name: 'Sibling', api: ['sensors'], size: [180, 120],
  }), null);
  writeApp('broken', '<<<', null);
  const mans = reg.loadAppManifests(appsDir, logFn);
  assert.ok(mans.some((m) => m.id === 'good'), 'good still loaded');
  assert.ok(mans.some((m) => m.id === 'sibling'), 'sibling still loaded');
  assert.ok(!mans.some((m) => m.id === 'broken'));
});

// resolveAppsDir: env wins
check('resolveAppsDir env', () => {
  const d = reg.resolveAppsDir({
    env: { JARVIS_APPS_DIR: appsDir, APPDATA: tmpRoot },
    repoDir: path.join(tmpRoot, 'repo-apps'),
  });
  assert.strictEqual(path.resolve(d), path.resolve(appsDir));
});

/** AABB helper for occupied-avoidance tests */
function assertNoOverlapPairs(rects, label) {
  for (let i = 0; i < rects.length; i++) {
    for (let j = i + 1; j < rects.length; j++) {
      assert.ok(!reg.rectsOverlap(rects[i], rects[j]),
        label + ' overlap ' + i + ' x ' + j);
    }
  }
}

// ① carousel + occupied (bottom-left stats-like) → cards clear
check('carousel avoids occupied', () => {
  const occupied = [{ x: 40, y: 800, w: 320, h: 245 }]; // left-bottom band
  const mans = [
    { id: 'c1', size: [220, 160] },
    { id: 'c2', size: [220, 160] },
  ];
  const layLogs = [];
  const placed = reg.layoutApps(mans, 'carousel', { width: 1920, height: 1080 }, (m) => layLogs.push(m), occupied);
  assert.strictEqual(placed.length, 2);
  for (const p of placed) {
    for (const o of occupied) {
      assert.ok(!reg.rectsOverlap(
        { x: p.x, y: p.y, w: p.w, h: p.h }, o
      ), 'card ' + p.id + ' hits occupied');
    }
  }
  assertNoOverlapPairs(placed.map((p) => ({ x: p.x, y: p.y, w: p.w, h: p.h })), 'carousel cards');
  assert.ok(layLogs.some((l) => /overlap resolve/.test(l)), 'expected resolve log');
});

// ② free + occupied → cards clear
check('free avoids occupied', () => {
  const occupied = [{ x: 0, y: 0, w: 200, h: 200 }];
  const mans = [
    { id: 'f1', size: [100, 80], x: 50, y: 50 }, // inside occupied
  ];
  const layLogs = [];
  const placed = reg.layoutApps(mans, 'free', { width: 800, height: 600 }, (m) => layLogs.push(m), occupied);
  assert.strictEqual(placed.length, 1);
  assert.ok(!reg.rectsOverlap(
    { x: placed[0].x, y: placed[0].y, w: placed[0].w, h: placed[0].h },
    occupied[0]
  ), 'free card still in occupied');
  assert.ok(layLogs.some((l) => /overlap resolve/.test(l)), 'expected resolve log');
});

// ③ 負控：occupied=[] → carousel identical to pre-occupied behaviour
check('carousel occupied=[] unchanged', () => {
  const mans = [
    { id: 'n1', size: [220, 160] },
    { id: 'n2', size: [180, 120] },
  ];
  const bounds = { width: 1920, height: 1080 };
  const a = reg.layoutApps(mans, 'carousel', bounds, () => {}, []);
  const b = reg.layoutApps(mans, 'carousel', bounds, () => {}); // omit occupied
  const y = Math.max(40, 1080 - 200);
  assert.strictEqual(a[0].x, 40);
  assert.strictEqual(a[0].y, y);
  assert.strictEqual(a[1].x, 40 + 220 + 12);
  assert.strictEqual(a[1].y, y);
  assert.strictEqual(a[0].x, b[0].x);
  assert.strictEqual(a[0].y, b[0].y);
  assert.strictEqual(a[1].x, b[1].x);
  assert.strictEqual(a[1].y, b[1].y);
});

try {
  fs.rmSync(tmpRoot, { recursive: true, force: true });
} catch (_) {}

if (failed) {
  console.log('\nFAILED: ' + failed);
  process.exit(1);
}
console.log('\nALL PASS');
process.exit(0);

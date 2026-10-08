'use strict';
/**
 * HUD app plugin registry (HoloMat H1).
 * Pure Node — no electron require (safe for unit tests + main.js).
 */
const fs = require('fs');
const path = require('path');

/** D4 whitelist — only these names may be exposed to apps. */
const API_WHITELIST = Object.freeze([
  'register', 'sensors', 'speak', 'alerts', 'media', 'settings', 'log',
]);

/** Always allowed without app.json api declaration. */
const API_ALWAYS = new Set(['register']);

/**
 * D1: resolve apps dir at CALL time (same pattern as settings_dir()).
 * JARVIS_APPS_DIR → %APPDATA%\Jarvis\apps (if exists) → repoDir.
 */
function resolveAppsDir(opts) {
  const env = (opts && opts.env) || process.env;
  const repoDir = (opts && opts.repoDir) || path.join(__dirname, 'apps');
  if (env.JARVIS_APPS_DIR) {
    return path.resolve(String(env.JARVIS_APPS_DIR));
  }
  const appdata = env.APPDATA;
  if (appdata) {
    const d = path.join(appdata, 'Jarvis', 'apps');
    if (fs.existsSync(d)) return d;
  }
  return repoDir;
}

function appErrorLogPath(env) {
  const e = env || process.env;
  return path.join(e.APPDATA || '', 'Jarvis', 'app_error.log');
}

function appendAppError(appId, msg, env) {
  const line = new Date().toISOString() + ' [' + (appId || '?') + '] ' + String(msg || '') + '\n';
  try {
    const p = appErrorLogPath(env);
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.appendFileSync(p, line, 'utf8');
  } catch (_) { /* never throw out */ }
  return line;
}

/**
 * Scan dir for app.json in each subfolder. Bad JSON / missing id → skip + log, never throw.
 */
function loadAppManifests(dir, logFn) {
  const log = typeof logFn === 'function' ? logFn : console.log;
  const out = [];
  if (!dir || !fs.existsSync(dir)) return out;
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch (e) {
    log('[apps] readdir fail: ' + (e && e.message ? e.message : e));
    return out;
  }
  for (const ent of entries) {
    if (!ent.isDirectory()) continue;
    const folder = path.join(dir, ent.name);
    const jsonPath = path.join(folder, 'app.json');
    if (!fs.existsSync(jsonPath)) continue;
    let raw;
    try {
      raw = fs.readFileSync(jsonPath, 'utf8');
    } catch (e) {
      log('[apps] skip ' + ent.name + ': read fail');
      appendAppError(ent.name, 'read app.json fail: ' + (e && e.message ? e.message : e));
      continue;
    }
    let man;
    try {
      man = JSON.parse(raw);
    } catch (e) {
      log('[apps] skip ' + ent.name + ': bad JSON');
      appendAppError(ent.name, 'bad JSON: ' + (e && e.message ? e.message : e));
      continue;
    }
    if (!man || typeof man !== 'object' || !man.id) {
      log('[apps] skip ' + ent.name + ': missing id');
      appendAppError(ent.name, 'missing id');
      continue;
    }
    // D7 v1: only primary
    if (man.monitor != null && String(man.monitor) !== 'primary') {
      log('[apps] skip ' + man.id + ': monitor=' + man.monitor + ' (v1 primary only)');
      continue;
    }
    const size = Array.isArray(man.size) ? man.size : [220, 160];
    out.push({
      id: String(man.id),
      name: man.name != null ? String(man.name) : String(man.id),
      icon: man.icon != null ? String(man.icon) : '◆',
      api: Array.isArray(man.api) ? man.api.map(String) : [],
      size: [Number(size[0]) || 220, Number(size[1]) || 160],
      x: man.x != null ? Number(man.x) : undefined,
      y: man.y != null ? Number(man.y) : undefined,
      monitor: man.monitor != null ? String(man.monitor) : 'primary',
      dir: folder,
      jsPath: path.join(folder, 'app.js'),
    });
  }
  return out;
}

function rectsOverlap(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

/**
 * D6 layout: carousel (auto band) or free (x/y) with overlap resolution.
 * occupied: existing HUD widgets {x,y,w,h}[] — both modes must avoid (never silent overlap).
 * On collision: nudge down then right until clear; log every move.
 */
function layoutApps(manifests, mode, bounds, logFn, occupied) {
  const log = typeof logFn === 'function' ? logFn : console.log;
  const GAP = 12;
  const bw = (bounds && bounds.width) || 1920;
  const bh = (bounds && bounds.height) || 1080;
  const list = Array.isArray(manifests) ? manifests : [];
  const occ = Array.isArray(occupied) ? occupied.filter((r) => r && Number.isFinite(r.x) && Number.isFinite(r.y) && r.w > 0 && r.h > 0) : [];
  const placed = [];

  function firstHit(cand) {
    for (let i = 0; i < occ.length; i++) {
      if (rectsOverlap(cand, occ[i])) return occ[i];
    }
    for (let i = 0; i < placed.length; i++) {
      if (rectsOverlap(cand, placed[i])) return placed[i];
    }
    return null;
  }

  function resolveSlot(id, startX, startY, w, h) {
    let x = startX;
    let y = startY;
    const origX = x;
    const origY = y;
    for (let i = 0; i < 200; i++) {
      const cand = { x: x, y: y, w: w, h: h };
      const hit = firstHit(cand);
      if (!hit) break;
      const downY = hit.y + hit.h + GAP;
      if (downY + h <= bh) {
        y = downY;
        x = hit.x;
      } else {
        x = hit.x + hit.w + GAP;
        y = hit.y;
        if (x + w > bw) {
          x = 40;
          y = hit.y + hit.h + GAP;
        }
      }
    }
    if (x !== origX || y !== origY) {
      log('[apps] overlap resolve ' + id + ' (' + origX + ',' + origY + ') -> (' + x + ',' + y + ')');
    }
    return { x: x, y: y };
  }

  if (mode !== 'free') {
    // carousel: bottom band, left → right; skip occupied / placed via resolveSlot
    let x = 40;
    const bandY = Math.max(40, bh - 200);
    for (const m of list) {
      const w = m.size[0];
      const h = m.size[1];
      const slot = resolveSlot(m.id, x, bandY, w, h);
      placed.push(Object.assign({}, m, { x: slot.x, y: slot.y, w: w, h: h }));
      x = slot.x + w + GAP;
    }
    return placed;
  }

  for (const m of list) {
    const w = m.size[0];
    const h = m.size[1];
    const startX = Number.isFinite(m.x) ? m.x : 40;
    const startY = Number.isFinite(m.y) ? m.y : 40;
    const slot = resolveSlot(m.id, startX, startY, w, h);
    placed.push(Object.assign({}, m, { x: slot.x, y: slot.y, w: w, h: h }));
  }
  return placed;
}

/** D4 gate: undeclared api → false (fail-loud caller writes log). */
function isApiAllowed(declaredApi, name) {
  const n = String(name || '');
  if (!API_WHITELIST.includes(n)) return false;
  if (API_ALWAYS.has(n)) return true;
  const list = Array.isArray(declaredApi) ? declaredApi : [];
  return list.indexOf(n) !== -1;
}

function readAppJs(jsPath) {
  try {
    return fs.readFileSync(jsPath, 'utf8');
  } catch (e) {
    return null;
  }
}

module.exports = {
  API_WHITELIST,
  API_ALWAYS,
  resolveAppsDir,
  loadAppManifests,
  layoutApps,
  rectsOverlap,
  isApiAllowed,
  appendAppError,
  appErrorLogPath,
  readAppJs,
};

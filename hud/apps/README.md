# JARVIS HUD Apps（HoloMat H1）

Drop a folder into the apps directory → HUD loads it. No rebuild, no version bump.

## Where

Resolution order (call-time, same idea as `settings_dir()`):

1. `JARVIS_APPS_DIR` (env, tests/dev override)
2. `%APPDATA%\Jarvis\apps` (production — if the folder exists)
3. `<repo>/hud/apps` (dev fallback)

Packed `app.asar` is read-only — always put user apps under `%APPDATA%\Jarvis\apps\`.

## Minimal app

```
my-widget/
  app.json    # required
  app.js      # optional; entry = function register(Jarvis) { … }
  README.md   # optional
```

### app.json

```json
{
  "id": "my-widget",
  "name": "My Widget",
  "icon": "◆",
  "api": ["sensors"],
  "size": [220, 160],
  "x": 80,
  "y": 120,
  "monitor": "primary"
}
```

| Field | Notes |
|---|---|
| `id` | Required. Missing / bad JSON → skip + `app_error.log` |
| `api` | Declare every API you call (`sensors` / `speak` / `alerts` / `media` / `settings` / `log`). Undeclared → blocked + log |
| `size` | `[w,h]` px |
| `x`/`y` | Free-layout coords (ignored in carousel mode) |
| `monitor` | v1: only `"primary"` (other values skipped) |

### app.js

```js
function register(Jarvis) {
  Jarvis.register({
    id: 'my-widget',
    mount(el) { el.textContent = 'hi'; },
    unmount() { /* clear intervals / listeners */ },
    tick() { return Jarvis.sensors().then((hw) => { /* update */ }); },
  });
}
```

## Jarvis API (whitelist)

| API | Needs `api` entry | Role |
|---|---|---|
| `register(spec)` | always | Mount into HUD card |
| `sensors()` | `sensors` | CPU/GPU/RAM/NET (hw_monitor) |
| `speak(text)` | `speak` | TTS |
| `alerts()` | `alerts` | Alert peek |
| `media()` | `media` | Media bridge state |
| `settings(name)` | `settings` | Read one settings key |
| `log(msg)` | `log` | Append app log |

**No** Node filesystem / process spawn / OS open-external / arbitrary IPC. Apps run in the renderer (no Node).

## Layout

Settings → **HUD Apps**：自動排列 (carousel) / 自由擺位 (free). Instant apply. Free mode resolves overlaps (nudge down/right + log) — silent overlap is forbidden.

## Reload

- Settings → **重新載入 apps** (v1 production path)
- Dev watcher: `JARVIS_APPS_WATCH=1` (debounce ~700ms)

## Errors

One bad app never kills the HUD. Failures go to `%APPDATA%\Jarvis\app_error.log` with the app id.

## Trust model

Whoever can write the apps directory can run code inside the HUD. Same trust class as Obsidian/VS Code plugins — not a sandbox.

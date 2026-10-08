# hw-ring

Sample HUD app (HoloMat H1). Shows CPU/GPU/RAM/NET load from `hw_monitor.py` via `Jarvis.sensors()`.

## Files

- `app.json` — manifest (`id`, `api:["sensors"]`, `size`)
- `app.js` — `function register(Jarvis) { … }`

## Drop-in

Copy this folder to `%APPDATA%\Jarvis\apps\hw-ring\` (or keep under `hud/apps/` for dev). Press **重新載入 apps** in Settings, or restart HUD.

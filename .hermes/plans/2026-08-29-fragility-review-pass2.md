# JARVIS + Hermes — Fragility Review Pass 2
**Date:** 2026-08-29  
**Scope:** architecture / robustness (“what breaks in 3 months?”)  
**Method:** read-only inspect of `jarvis-pc` sidecar, `jarvis-hud` Electron, Hermes scripts/state, live `%APPDATA%\Jarvis` + `%LOCALAPPDATA%\hermes\state`  
**Not:** line-by-line style review · **No files edited**

---

## Verdict (one line)

System works as a **single-machine, path-pinned, multi-writer state machine**. Highest 3-month pain = **host binding + settings races + Electron SPOF**, not clever bugs in wake math.

Label legend: **FACT** = observed in code/state · **INFERENCE** = likely failure mode · **OPINION** = priority judgment.

---

## Top 10 (probability × impact)

### 1. Hardcoded host binding (Python 3.14 + jarvis-pc paths)
**Score:** P=high · I=catastrophic  

**WHY in 3 months:**  
**FACT:** `jarvis-hud/main.js` hardcodes  
`SIDECAR_PY = C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\python.exe` and  
`JARVIS_PC_DIR = C:\Users\skps9\Documents\Code_Project\jarvis-pc` (comment admits portable exe still depends on this).  
Same Python path repeated for `PYTHON` / mic loops / activity / hw.  
**INFERENCE:** Windows Store / python.org minor bump, folder move, or new PC → spawn fails or runs wrong tree. Crash-loop balloon fires; voice dead. Packaged HUD does **not** ship the sidecar.

**Cheapest mitigation:** One env/config file (e.g. `%APPDATA%\Jarvis\host.json` or `JARVIS_PYTHON` + `JARVIS_PC_DIR`) read at startup; fail loud in tray if missing. Drop absolute user path from source.

---

### 2. `settings.json` multi-writer races (no lock, non-atomic merge)
**Score:** P=high · I=high  

**WHY:**  
**FACT:** Three writers, no shared lock:
1. Electron `settings:save` — read → merge → `writeFileSync` (`main.js` ~731–738)  
2. Python `save_settings()` — read → `{**existing, **asdict(s)}` → `write_text` (`settings.py` ~518–535)  
3. `self_monitor._write_wake_threshold` — copy bak → rewrite whole JSON (`self_monitor.py` ~142–160)  

**INFERENCE:** Concurrent Electron save + daily threshold tune → lost keys (API keys, device names, toggles). Corrupt/partial write possible (Python path not tmp+replace; Electron sync write better but still race).  
**FACT:** Electron save does **not** notify sidecar / call `apply_settings` — disk updates; in-memory wake/hotkey/alerts may stay stale until process restart.

**Cheapest mitigation:** Single writer API (sidecar HTTP `POST /settings` with dir-lock + tmp+replace). Electron only posts patch. Self-monitor posts `{wake_threshold}` only. Until then: document “restart serve after settings save.”

---

### 3. ML / audio dependency drift on system Python 3.14
**Score:** P=high · I=high  

**WHY:**  
**FACT:** Runtime = system 3.14, not venv. `pyproject.toml`: `torch>=2.0` / `torchaudio>=2.0` **unupper-bounded**; `funasr`, `onnxruntime`, `openwakeword` loosely capped. **`pyaec` / `pyaudiowpatch` / `speechbrain` not declared** in extras (only comments in `aec.py` / docs).  
**INFERENCE:** One `pip install -U torch|transformers|funasr` or onnxruntime DLL churn → SenseVoice / OWW / Piper / AEC / speaker gate die. Python 3.14 still bleeding-edge for wheels.  
**FACT:** `mage_engine.py` uses `trust_remote_code=True` + **monkeypatches** `dynamic_module_utils.check_imports = lambda filename: []` — transformers or Mage-VL snapshot change → load breaks or silently skips safety.

**Cheapest mitigation:** Freeze a `requirements-lock.txt` (or uv lock) for the audio stack; pin torch/cuda build; add `[project.optional-dependencies] aec` / `speaker` with pins. Comment in README: never `pip upgrade` without smoke. Mage: pin model revision hash + stop blanking `check_imports` long-term.

---

### 4. Electron is the watchdog SPOF (post–jarvis-cron removal)
**Score:** P=medium-high · I=high  

**WHY:**  
**FACT (instruction + code):** Jarvis cron removed 2026-08-29; sidecar spawn + 30s TCP health on `:8765` + crash-loop backoff live in `main.js` (`spawnSidecar` / `startSidecarHealthCheck`).  
**INFERENCE:** Electron crash / user Force End Task / failed auto-start → no process restarts jarvis. Health = **TCP connect to 8765 only** — anything listening (stale MCP, wrong process) counts as “up”; true hang with port held looks healthy. Balloon notify once per loop episode — easy to miss.  
**FACT:** Hermes activity cron still separate (`hermes/cron/jobs.json` → `activity_watch.py`); jarvis voice does not.

**Cheapest mitigation:** Keep a tiny OS-level Task Scheduler / hermes `no_agent` job that only ensures `jarvis serve` OR Electron ONE is up (not full alert stack). Health probe `GET http://127.0.0.1:8765/health` (already exists on MCP) not bare TCP.

---

### 5. Audio device identity is brittle (names, truncation, exact match)
**Score:** P=high · I=medium-high  

**WHY:**  
**FACT (live `settings.json`):** `wake_mic_device` = `"麥克風 (2- Arctis Nova 7)"`; `tts_output_device` = `"G27Q (NVIDIA High Definition Au"` (**truncated**).  
**FACT:** `mouth._resolve_output_device` requires **exact** name equality (`str(d.get("name")) != name` → miss → `None` → system default). USB/Sonar/Windows renumbering or longer display names → silent wrong speaker or mic.  
**FACT:** AEC defaults / UI placeholders assume SteelSeries Sonar Media/Chat; `shell_app` hardcodes extra loopback needle `"SteelSeries Sonar - Chat"`. New headset or Sonar update → AEC under-cancels → FP wakes.

**Cheapest mitigation:** Store stable IDs where possible; resolve by **prefix/contains** + log mismatch warning to `serve.log` / tray once. Fix truncated TTS name on next settings save; reject names that don’t resolve at save time.

---

### 6. `sk_activity.json` dual-path drift (cron write vs HUD live exec)
**Score:** P=medium · I=high (gates + AGENTS policy)  

**WHY:**  
**FACT:** Hermes cron `sk-activity-monitor` → `activity_watch.py` → `activity_monitor.py --update` writes JSON (alive: `last_run_at` 2026-08-29, file timestamp fresh).  
**FACT:** HUD `checkActivity` runs `activity_monitor.py` **without** `--update` every 5s (stdout only). Sidecar gates (`activity.py`, voice-call mute, GPU policy, game-ready) read **JSON**.  
**INFERENCE:** Cron disabled / Hermes scheduler down → JSON goes stale while HUD still hides dock from live stdout. Agents reading JSON for GUI gate → wrong `idle`/`playing`. Voice-call mute / wake pause lag up to ~1 min even when healthy.

**Cheapest mitigation:** HUD also call `--update` (or write JSON itself) **or** sidecar exec monitor / share one writer. Add `timestamp` age check: if >3 min stale → treat as `using` (conservative) + one log line.

---

### 7. Silent degradation: AEC skip + speaker_gate fail-open + voice_status soft state
**Score:** P=high · I=medium  

**WHY:**  
**FACT:** `wake._apply_aec` — exceptions `pass`; missing loopback → `_aec_skipped++` with no user alert.  
**FACT:** `speaker_gate.verify_pcm` — `no_profile` / `model_fail` / `encode_fail` → `accept=True, skip=True` (fail-open). Live settings: `speaker_gate: false` already.  
**FACT:** `voice_status.json` uses wall-clock `ts: "HH:MM:SS"` only (no epoch/date); Electron poll diffs content, never marks stale. Sidecar dead → HUD may show last “就緒 / wake_on” forever.  
**INFERENCE:** Three months of quiet FP wakes / wrong HUD status with no balloon.

**Cheapest mitigation:** If `_aec_skipped` rate high or gate always `skip`, write `voice_status.degraded` + tray once/day. Add ISO `updated_at` to voice_status; HUD greys status if age >30s.

---

### 8. Hermes bridge auth + API surface coupling
**Score:** P=medium · I=high when hermes_enabled  

**WHY:**  
**FACT:** Bearer key in `%APPDATA%\Jarvis\hermes_api.key` (`load_or_create_api_key`); API hardcoded `127.0.0.1:8642`; chat path `POST /v1/runs` + SSE consume; on mismatch can `_kill_api_port` / restart gateway.  
**FACT:** Settings also have `hermes_base_url` default `:8688` (UI/open browser) — **different port** from API `:8642` (easy confusion).  
**INFERENCE:** Hermes agent upgrade changing Runs/SSE/auth → jarvis voice brain dead. Aggressive port kill races Discord gateway. No documented rotation path for MCP bearer (`mcp_token.txt` auto-mint) vs Hermes key.

**Cheapest mitigation:** Version-pin Hermes API client; probe capabilities before kill; never kill port unless PID owned by known gateway command line. One-page “auth files map” in docs. Rotate = delete key file + restart both sides.

---

### 9. Secrets + plaintext settings as footgun
**Score:** P=medium · I=high (security / accidental leak)  

**WHY:**  
**FACT:** Live `settings.json` holds LLM/ASR API keys in cleartext under Roaming (also mirrored legacy `mimo_*`). Electron settings UI loads them into DOM.  
**INFERENCE:** Backup sync, screen share, agent logs dumping settings, or git of AppData copy → credential leak. No rotation UX. (Keys observed during review — **not reproduced here**.)

**Cheapest mitigation:** Move secrets to DPAPI / Windows Credential Manager or `%APPDATA%\Jarvis\secrets.json` gitignored; settings UI show masked + “replace only”; scrub keys from serve.log.

---

### 10. Iteration blockers: mega-modules + dual settings UI
**Score:** P=certain (ongoing) · I=medium (regression tax)  

**WHY:**  
**FACT:** `shell_app.py` ~1850 lines (wake, alerts, MCP, HUD push, self-monitor, voice-call, game watch, tray). `main.js` ~900 lines (sidecar, ports 8770/8771, activity, dock, settings IPC). `settings.html` ~40+ fields; **tk** `settings_ui.py` still exists beside Electron settings.  
**INFERENCE:** Next feature (new alert source, new gate, new vision path) almost always touches `shell_app` + `settings.py` + `settings.html` + maybe `main.js` clamp — high regression chance. Clamp duplicated (Python `_clamp` vs JS `clampSettingsPatch`) will drift.

**Cheapest mitigation:** Stop growing `shell_app` — new behavior in modules + thin wire-up. Kill or freeze tk settings when Electron is source of truth. Generate clamp from one schema. One smoke test: save settings → sidecar `/health` reflects wake_on within N seconds.

---

## Axes checklist (short)

| Axis | Hottest finding # |
|------|-------------------|
| Dependency drift | 3, Mage remote-code |
| Hardcoded assumptions | 1, 5, ports 8765/8770/8771/8642/8688 |
| Silent failure | 7, health=TCP only |
| State/consistency | 2, 6, queue.jsonl has lock (better than settings) |
| Hermes coupling | 8; activity cron still Hermes (6) |
| SPOF | 4 |
| Iteration blockers | 10 |

**Note — alert queue:** `AlertStore` uses dir-lock + tmp+replace (**FACT**) — less fragile than settings; skip from top-10 unless lock steal races under load.

**Note — self-monitor threshold:** writes disk daily; wake thread started with in-memory thr — **INFERENCE:** tune may wait until next serve restart unless something reloads wake. Amplifies #2/#7.

---

## Top 3 to fix first

1. **Host config out of source** (#1) — unblocks any machine move / python bump; 30–60 min.  
2. **Settings single-writer + apply hook** (#2) — stops silent config loss and “saved but not live” wake/TTS.  
3. **Electron SPOF health** (#4) — `/health` probe + one external ensure-alive job; prevents “HUD closed = house deaf.”

Everything else (pins, device resolve, activity single writer, degrade flags) stacks on these.

---

## Evidence index (paths)

- `jarvis-hud/main.js` — SIDECAR_PY, spawn/health, settings:save, checkActivity, ports 8770/8771  
- `jarvis-pc/src/jarvis/settings.py` — save/load merge  
- `jarvis-pc/src/jarvis/self_monitor.py` — threshold rewrite  
- `jarvis-pc/src/jarvis/wake.py` / `aec.py` / `speaker_gate.py` / `mouth.py` — AEC skip, fail-open, exact TTS name  
- `jarvis-pc/src/jarvis/hermes_bridge.py` — :8642, key file, /v1/runs  
- `jarvis-pc/src/jarvis/mage_engine.py` — trust_remote_code + check_imports patch  
- `jarvis-pc/pyproject.toml` — loose ML pins; missing pyaec/speechbrain  
- `%LOCALAPPDATA%\hermes\cron\jobs.json` — `sk-activity-monitor` still enabled  
- `%LOCALAPPDATA%\hermes\scripts\activity_monitor.py` / `activity_watch.py`  
- Live state: `%APPDATA%\Jarvis\settings.json`, `voice_status.json`; `%LOCALAPPDATA%\hermes\state\sk_activity.json`

---

*End pass 2. No code changes made.*

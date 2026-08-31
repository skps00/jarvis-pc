# QA Report: jarvis-pc (Hermes alerts / Cursor hooks)

| Field | Value |
|-------|-------|
| **Date** | 2026-08-09 |
| **URL** | n/a (desktop companion + loopback MCP; no web UI) |
| **Branch** | feature/hermes-alerts-mcp |
| **Commit** | 9723495 (2026-08-09 16:03 +0800) |
| **PR** | #11 (https://github.com/skps00/jarvis-pc/pull/11) |
| **Tier** | Standard |
| **Scope** | Diff-aware: alerts MCP, Cursor hooks, companion settings/shell |
| **Duration** | ~8 min |
| **Surfaces checked** | pytest (46), hook script sims (4), live MCP :8765, hooks install status, process/port probe |
| **Screenshots** | 0 (no browsable UI; cursor-ide-browser MCP unavailable) |
| **Framework** | Python / Tk companion + FastMCP HTTP |
| **Mode** | Diff-aware (feature branch, no URL) |

## Health Score: 91/100

| Category | Score | Notes |
|----------|-------|-------|
| Console | 100 | No runtime errors in MCP init / hook sims |
| Links | 100 | N/A web links |
| Visual | 70 | Tk companion UI not screenshot-verified this run |
| Functional | 92 | Core paths green; AskQuestion hook gap is upstream |
| UX | 90 | Suppress false-finished verified in sim |
| Performance | 100 | Tests 2.1s; MCP init OK |
| Content | 100 | Phrases match design (plan / approval / finished) |
| Accessibility | 85 | Exact UIA wait remains fallback; not re-probed live |

Weighted: ≈91.

## Top 3 Things to Fix

1. **ISSUE-001: AskQuestion often skips Cursor hooks** — upstream; UIA fallback still required for plan/ask pings.
2. **ISSUE-002: pytest not a project dependency** — `uv run pytest` fails; need `uv run --with pytest`.
3. **ISSUE-003: Tk companion visual smoke skipped** — no browser surface; defer manual/CUA smoke of settings UI.

## Console Health

| Error | Count | First seen |
|-------|-------|------------|
| (none in hook/MCP probes) | 0 | — |
| pydantic IncompleteFieldDefinitionWarning `lifespan` | 1 | `tests/test_mcp_alerts_http.py` |

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 2 |
| **Total** | **3** |

## Changes tested (diff vs main)

- Alert store + poller + speak_once path
- HTTP alerts MCP (`:8765/mcp`, Bearer)
- Cursor `stop` + `preToolUse` hooks → queue
- Suppress `stop→finished` after approval tool / waiting latch
- Settings / shell companion wiring
- Regression tests under `tests/test_*alert*`, `test_cursor_hooks.py`

**Live runtime (FACT):** `jarvis serve` + `mcp_alerts_http :8765` + poller process up; ports 3000/4000/8080 down (expected).

**Hooks (FACT):** `python -m jarvis cursor-hooks status` → installed stop=yes, preToolUse=yes; `~/.cursor/hooks.json` exists.

## Issues

### ISSUE-001: AskQuestion may not fire preToolUse

| Field | Value |
|-------|-------|
| **Severity** | medium |
| **Category** | functional |
| **URL** | Cursor agent (not jarvis-owned) |
| **Fix Status** | deferred (upstream) |

**Description:** Cursor often ends turn with `stop status=completed` when waiting on Ask/plan. AskQuestion frequently skips tool hooks. Our suppress window only helps when `preToolUse` *does* fire, or companion UIA exact `Waiting for approval` marks waiting.

**Evidence:** Documented in `scripts/cursor_hook_alert.py` header; prior session user reports; not re-exercised in live Cursor UI this run.

**Repro (manual):** Enter plan/Ask wait without SwitchMode hook → may hear false “finished” or silence on approval depending on UIA.

---

### ISSUE-002: pytest missing from project env

| Field | Value |
|-------|-------|
| **Severity** | low |
| **Category** | ux (developer) |
| **Fix Status** | deferred |

**Description:** `.\.venv\Scripts\python.exe -m pytest` → No module named pytest. `uv run pytest` → program not found. Works with `uv run --with pytest python -m pytest …`.

**Evidence:** Command output this session. 46 tests passed once pytest injected.

---

### ISSUE-003: No visual QA of companion window

| Field | Value |
|-------|-------|
| **Severity** | low |
| **Category** | visual |
| **Fix Status** | deferred |

**Description:** gstack `/qa` browse path not applicable; `cursor-ide-browser` MCP not available. Tk settings/shell not screenshot-verified.

---

## Verification evidence (no screenshots)

### Unit / integration

```
uv run --with pytest python -m pytest \
  tests/test_alert_store.py tests/test_alert_tts_sink.py tests/test_alerts.py \
  tests/test_cursor_hooks.py tests/test_mcp_alerts_http.py \
  tests/test_settings.py tests/test_shell_wake_restart.py -q
→ 46 passed, 1 warning in 2.10s
```

### Isolated hook sims (temp APPDATA — no TTS)

| Scenario | Expected | Result |
|----------|----------|--------|
| stop completed | enqueue “Cursor finished its work.” | PASS |
| SwitchMode then stop | plan phrase only; finished suppressed | PASS |
| AskQuestion then stop | approval phrase only; finished suppressed | PASS |
| stop aborted | no enqueue | PASS |

### Live MCP

- Without Bearer → HTTP 401 (expected)
- With token from `%APPDATA%\Jarvis\alerts\mcp_token.txt` → initialize 200, server `jarvis-alerts`

## Fixes Applied

| Issue | Fix Status | Commit | Files Changed |
|-------|-----------|--------|---------------|
| ISSUE-001 | best-effort (mitigate; upstream AskQuestion still skips hooks) | uncommitted | `src/jarvis/alerts.py`, `tests/test_cursor_hooks.py` |
| ISSUE-002 | verified | uncommitted | `pyproject.toml` (+ uv.lock) |
| ISSUE-003 | verified (headless build smoke) | uncommitted | `tests/test_settings_ui_smoke.py` |

### Fix notes

- **ISSUE-001:** While UIA exact `Waiting for approval` is visible, refresh `mark_waiting()` every poll so suppress does not expire mid-wait. Cannot make Cursor fire AskQuestion hooks.
- **ISSUE-002:** `uv sync --group dev` then `uv run pytest` works.
- **ISSUE-003:** Settings window builds 4 tabs under withdrawn Tk root.

## Regression Tests

Existing suite already covers suppress / enqueue / MCP 401. No new regression files this run.

## PR Summary

> QA found 3 issues (0 fixed), health score 91. Diff-aware: 46 tests pass; hook suppress + live MCP OK. AskQuestion hook gap remains upstream/deferred.

## Notes / concerns

- FACT: Working tree clean at QA start.
- INFERENCE: Running `jarvis serve` may still be older process if not restarted after last pull — restart companion if behavior mismatches HEAD.
- OPINION: Treat this report as code-path QA, not full desktop UX QA.

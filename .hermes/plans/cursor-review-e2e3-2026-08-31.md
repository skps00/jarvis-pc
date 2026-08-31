# Cursor Code Review — JARVIS E2/E3 + 脆弱位修復（2026-08-31）

REVIEW ONLY. No code edited. Findings from reading the batch listed in the review brief.

---

## Findings

### 1. HIGH — `_compute_latency` treats midnight `0.0` as missing

**Where:** `src/jarvis/self_monitor.py:199`

```python
if not ft or not tt:
    return None
```

**FACT:** `_hms_to_sec("00:00:00 …")` returns `0.0`. In Python, `not 0.0` is `True`.

**Impact:** Fire or `tts_ok` at exactly `00:00:00` drops latency to `None` (shows `n/a`). Midnight-crossing path (`+86400`) is tested for `23:59:58 → 00:00:01`, but not for a zero second-of-day on either side.

**Fix:** Use explicit None checks:

```python
if ft is None or tt is None:
    return None
```

Add test: fire `00:00:00` + tts `00:00:03` → `3.0`.

---

### 2. HIGH — `repair_ratio` mixes unbounded repair_log with tailed wake window

**Where:** `src/jarvis/stt_stats.py:76` (`load_repair_events` full-file read) + `:191–194` (`run_once`)

**FACT:**
- `fires` = `oww_fire` count in last 2000 wake lines (`_tail_lines`).
- `pairs` = **all** rows in `repair_log.jsonl` (no tail / no time filter).
- Fallback `parse_repair_pairs(_tail_lines(serve))` *is* windowed.

**Impact:** As `repair_log.jsonl` grows, `repair_hits / fires` inflates (often ≫ 1). Fingerprint `REPAIR_RATIO` and suggestions become wrong once the structured log is preferred. Engine writer (`engine.py:50–66`) appends forever with no rotation.

**Fix (pick one consistent window):**
1. Tail / time-filter `repair_log.jsonl` to the same horizon as wake (e.g. last N lines or last 24h via `ts`), **or**
2. Count fires over the full overlapping period, **or**
3. Rotate/truncate repair_log and document the window.

Add a test: many historical jsonl rows + few recent wake fires must not yield ratio ≫ 1 under the chosen policy.

---

### 3. MED — Latency pairs last fire with last TTS; docstring overclaims “alert/ack filter”

**Where:** `src/jarvis/self_monitor.py:195–206`, `:76–82`, `:133–138`

**FACT:** Metric is “most recent `oww_fire` HH:MM:SS” vs “most recent `tts_ok` HH:MM:SS” across two independent logs. Filter is only `0 < dt ≤ 60` (plus midnight adjust). No correlation by utterance / session id.

**Impact:** Alert/ack/game-ready TTS within 60s after a wake fire is counted as response latency. True wake→reply latency can be replaced by unrelated TTS. Docstring claim “alert/ack 等其他 TTS 會過濾” is stronger than the code.

**Fix:** Keep heuristic honest in the docstring; optionally require `tts_ok` to follow fire and prefer the first `tts_ok` after fire in the serve window (still heuristic), or tag mouth prints with a correlator later. Do not claim hard filtering until that exists.

---

### 4. MED — `str(game).capitalize()` mangles acronyms / multi-word titles

**Where:** `src/jarvis/shell_app.py:1688`

**FACT:** `str.capitalize()` lowercases the rest of the string: `"CS2" → "Cs2"`, `"GTA V" → "Gta v"`, `"Team Fortress 2" → "Team fortress 2"`.

**Impact:** Spoken game-ready alerts sound wrong for common short titles.

**Fix:** Prefer title-case that preserves all-caps tokens, or only uppercase the first character: `game[:1].upper() + game[1:]` if `game` is non-empty, or leave the activity string unchanged if already display-ready.

---

### 5. MED — `_consecutive_days` ignores `detect_trend(..., window=)`

**Where:** `src/jarvis/self_review.py:120–122`, `:137–146`

**FACT:** `detect_trend` uses caller `window` for length/values, but `_consecutive_days` always slices `days[-_TREND_WINDOW:]` (hardcoded 3).

**Impact:** Today all callers use default `_TREND_WINDOW`, so production path is fine. Any future `window≠3` can mark a trend on a non-calendar-consecutive `window` while only validating the last 3 calendar days.

**Fix:** Pass `window` into `_consecutive_days` and slice `days[-window:]`. Extend the missing-days test to a custom window if the API stays public.

---

### 6. MED — Silent swallow on repair_log write failure

**Where:** `src/jarvis/engine.py:65–66`

**FACT:** `OSError` on mkdir/append is `pass`. stt_stats then falls back to serve.log text only when jsonl yields **zero** pairs (`stt_stats.py:193–194`).

**Impact:** If the file exists with older rows but new appends fail (disk full, ACL), stats look “healthy” on stale jsonl and never fall back to fresh `serve.log` lines. No counter/log for write failures.

**Fix:** Log once at warning (or increment a fail counter visible in serve.log) on write failure; consider falling back when jsonl mtime/size stalls. Optional: if jsonl is non-empty but older than newest serve `asr_repair`, merge or prefer serve for the overlapping window.

---

### 7. MED — Missing tests for several new / critical paths

**Coverage gaps (FACT: no matches in `tests/` for these):**

| Gap | Why it matters |
|---|---|
| `engine._log_repair_event` | No test that note → jsonl row shape / first-arrow-only / OSError swallow |
| `self_monitor` `lat_fmt_err` → `resp_lat=ERR` + `notable` | Fail-visible format drift is the point of ⑭; only helper counters tested |
| `self_review.main` unparseable log → stdout `ERROR` / exit 2 | ① + fp cron contract untested at CLI boundary |
| Midnight `00:00:00` latency (finding 1) | Truthiness bug uncaught |
| repair_log vs wake window (finding 2) | Ratio correctness uncaught |
| `shell_app` game phrase capitalize | Acronym regression untested |

Helpers for E3 (`_hms_to_sec`, parse, `_compute_latency` non-zero midnight cross) and E2 parse/fingerprint **are** covered. Consecutive-day guard **is** covered in `tests/test_self_review.py`.

**Fix:** Add the smallest tests above; prioritize findings 1–2 and `lat_fmt_err` / `main` ERROR.

---

### 8. LOW — Module docstring / plans still describe serve.log-first E2

**Where:** `src/jarvis/stt_stats.py:1–6`; `.hermes/plans/REMAINING_WORK.md` E2 blurb still emphasizes serve.log.

**Impact:** Next agent may “fix” the wrong primary path or reintroduce format coupling.

**Fix:** Docstring + plan line: primary = `repair_log.jsonl`, serve.log = fallback.

---

### 9. LOW — `_tail_lines` still full-file read in stt_stats / self_monitor

**Where:** `stt_stats.py:50–58`, `self_monitor.py:51–59` vs `self_review.py:47–56` (deque maxlen).

**Impact:** Large `serve.log` / `wake_debug.log` → memory spike on daily monitor. Known class of issue; self_review already fixed.

**Fix:** Reuse deque-tail pattern (same as self_review) when touching these again.

---

### 10. LOW — `jarvis_self_review_fp.py` ERROR branches look correct for spam fix

**Where:** `C:\Users\skps9\AppData\Local\hermes\scripts\jarvis_self_review_fp.py:34–43`

**FACT:** Exception / empty stdout → deterministic `ERROR` only (no stderr detail on stdout). Aligns with `self_review.main` parse-fail `print("ERROR")`.

**Note:** Wrapper always `return 0`; monitor must key off fingerprint text change, not process exit code. By design for ⑫; document if not already in cron comments.

No change required for the stated goal.

---

### 11. LOW — Docs in batch are auth/settings maps, not E2/E3 logic

**Where:** `docs/hermes-bridge-auth.md`, `docs/settings-field-map.md`

No secrets pasted. `settings-field-map` cites main.js line numbers that will drift — acceptable for a field map if treated as hints. Not blocking for E2/E3.

---

## What looks solid

- First-arrow-only repair pair parsing (serve + engine regex aligned).
- `lat_fmt_err` when **all** `tts_ok` lack timestamps → `ERR` + notable (⑭).
- Midnight **negative dt** `+86400` with 0–60s clamp (⑮) — works when both sides are non-zero.
- `_consecutive_days` gap rejection + tests (`test_trend_not_flagged_with_missing_days`).
- Suggestions never auto-applied; `extract_alias_target` gated.
- `eval_gate.GOLDEN_SUITES` includes `test_stt_stats.py`, `test_self_monitor.py`, `stt_stats.py` py_compile — matches golden-set.md listing.
- mouth.py both success paths print `tts_ok HH:MM:SS`.

---

## Summary counts

| Severity | Count |
|---|---|
| HIGH | 2 |
| MED | 5 |
| LOW | 4 |

Priority fix order: **#1** (None-check), **#2** (aligned windows / rotation), then **#7** tests locking those, then **#3/#4**.

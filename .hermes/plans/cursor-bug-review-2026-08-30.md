# Cursor Bug Review 2026-08-30

Review scope: Self-Evol Task 0–9 modules + `asr_repair` early-repair block + listed tests.
Method: full-file static read; no edits; no fixes run. Shell probes for `_GARBLED_PREFIX` were attempted but blocked in this session — ASR finding below is from regex/`_force_close_*` logic trace only.

## Summary

- **total findings: 11** (C=0 H=4 M=5 L=2)
- No CRITICAL (no remote RCE / secret exfil in these modules as reviewed).
- Clean enough to call out: `tests/test_eval_gate.py`, `tests/test_prompt_pipeline.py`, `tests/test_self_review.py`, `tests/test_settings_ui_smoke.py`, `tests/test_brain.py` (Hermes mocks) — no correctness bugs found beyond items below.
- `eval_gate.py` / `self_review.py` core algorithms mostly sound; issues are env/encoding/IO and autonomy/clarify design holes.

## Findings

### [HIGH] Early garbled-repair bypasses shellish when Discord/MC/WhatsApp tokens present
- file: `src/jarvis/asr_repair.py:424-427` (uses `_force_close_known` → `_force_close_discord` / `_force_close_mc` / `_force_whatsapp_open_close`)
- what is wrong: New block runs **before** `_looks_shellish`. Any string matching `_GARBLED_PREFIX` (e.g. leading `|`, `-`, `_`, `]`, `[`) that also contains a Discord/MC/WhatsApp-like token is rewritten to `閂 Discord` / `閂 minecraft` / open-or-close WhatsApp and **returned**, never reaching the shellish guard.
  - Quote: `if _GARBLED_PREFIX.match(raw): forced_early = _force_close_known(raw); if forced_early: return forced_early, ...`
  - `_SHELLISH` includes `\|` and `curl\s` (`memory.py:85-87`), so e.g. `|curl https://discord.gg/x` is shellish, but early path still forces `閂 Discord` because `\bdiscord\b` matches inside `discord.gg`.
- why it matters: Pasted shell/pipeline text with a Discord invite (or MC name) becomes a **close-app command** instead of being left alone. Opposite of comment claim that true shell lines are unaffected.
- suggested fix: Only early-return when forced repair is a **short STT garbled close** (e.g. require close-hint / short length / no `curl|wget|https?://|rm\s`), **or** still call `_looks_shellish` first and only bypass shellish for utterances that match a tight garbled-close pattern like `^[|\]\[\-_]{1,3}\s*(dico|disco|discord|...)\s*$`.

### [HIGH] `proceed()` drops conservative assumptions for asked-but-unanswered unknowns
- file: `src/jarvis/clarify.py:195-198`
- what is wrong: `unresolved = [u for u in self.u.unknowns if u.id not in self._asked_ids]`. IDs enter `_asked_ids` in `next_round()` when questions are **posed**, not when answered. There is no `record_answer` / resolve API. Asked unknowns are excluded from fallback assumptions.
- why it matters: Round 1 asks 5 impactful delete questions; user abandons; `proceed()` only assumes for the 1 never-asked unknown. The 5 asked delete-scope unknowns get **no**「唔刪除」assumption — contradicts “Fallback: proceed-with-assumptions”.
- suggested fix: Track `_answered_ids` separately; unresolved = not answered (or still in `u.unknowns`). On `proceed()`, apply `conservative_assumption` to every still-open unknown, asked or not.

### [HIGH] `next_round` asks non-impactful unknowns (EVPI violation)
- file: `src/jarvis/clarify.py:181-182` (+ `select_questions` does not filter `impact`)
- what is wrong: `fresh = [u for u in self.u.unknowns if u.id not in self._asked_ids]` includes `impact=False`. `select_questions` ranks impactful first but **fills the cap with non-impactful**. Module doc / `should_ask` say ask only when an unknown changes the action.
- why it matters: After impactful Qs are exhausted, round 2 still burns fatigue budget on questions that cannot change the plan (Alexa fatigue rationale in module header).
- suggested fix: `fresh = [u for u in self.u.unknowns if u.id not in self._asked_ids and u.impact]`; if empty → `return None` (force proceed).

### [HIGH] Autonomy promote skips L1a sandbox (`L0 → L1B`)
- file: `src/jarvis/autonomy.py:155-160`
- what is wrong: `nxt = {L0: L1B, L1A: L1B, L1B: L1C}.get(self.level)` jumps L0 straight to L1B. Docstring says “Promote ONE step”; `LEVELS = (L0, L1A, L1B, L1C)`; header defines L1a as sandbox isolation before L1b auto-apply.
- why it matters: First successful promotion enables **low-risk auto-apply (L1b)** without ever earning sandbox-only L1a. Undermines R10 ladder and sandbox prerequisite.
- suggested fix: `nxt = {L0: L1A, L1A: L1B, L1B: L1C}.get(self.level)`; keep L1c human-gated / non-auto-promote as now.

### [MEDIUM] `DEMOTE_THRESHOLD` defined but never used
- file: `src/jarvis/autonomy.py:57-58`, `163-169`
- what is wrong: Hysteresis story requires promote 0.90 / demote 0.85, but `demote()` only checks target is lower — no composite score gate. `DEMOTE_THRESHOLD` is dead.
- why it matters: Callers must invent demotion policy; “hysteresis” is only half-implemented. Easy to demote on noise or never demote on score alone.
- suggested fix: Either wire `demote_if_needed(evidence)` that demotes when `composite() < DEMOTE_THRESHOLD`, or remove the constant and document demotion as reason-driven only.

### [MEDIUM] `apply_optimized` docs say “introduces” but code absolute-scans body
- file: `src/jarvis/prompt_pipeline.py:41-47`, `117-132`
- what is wrong: Header: “if an optimized prompt INTRODUCES any of these compared to the original”. Implementation: `hits = scan_sensitive(body)` with no diff vs `original`. Any legitimate goal/acceptance text containing `token` / `api_key` / `輸出到…` rejects even a no-op optimize.
- why it matters: False jailbreak detections → optimizer never applies; or authors strip real constraints to pass the gate.
- suggested fix: `hits = set(scan_sensitive(body)) - set(scan_sensitive(original.replace(INVARIANT_BLOCK, "")))` (or line-diff new lines only).

### [MEDIUM] `format_simple` crashes / injects on `{` in goal
- file: `src/jarvis/prompt_pipeline.py:95-105`
- what is wrong: `_SIMPLE_TEMPLATE.format(goal=goal, output_format=output_format)`. User/ASR text with `{...}` raises `KeyError`/`ValueError`, or can substitute `output_format` if goal embeds that field name.
- why it matters: Voice/task strings are untrusted (R16/R17); braces appear in code snippets. Formatter should not throw.
- suggested fix: Use `template.replace("{goal}", goal).replace("{output_format}", output_format)` or `string.Template` with `$goal`.

### [MEDIUM] Eval subprocess `text=True` without UTF-8 on Windows
- file: `src/jarvis/eval_gate.py:103-105`
- what is wrong: `subprocess.run(..., text=True, env=env)` inherits Windows ANSI/cp1252. Suite paths/output often contain Unicode (tests assert Chinese captions elsewhere).
- why it matters: Golden suite can `UnicodeDecodeError` or mojibake detail → false FAIL of execution gate.
- suggested fix: `text=True, encoding="utf-8", errors="replace"` (and keep `env.pop("PYTHONPATH")` as now).

### [MEDIUM] `self_review._tail_lines` reads whole log into memory
- file: `src/jarvis/self_review.py:47-55`
- what is wrong: `path.read_text(...)` then slice last N. `_TAIL_LINES = 2000` lines but file may be huge (years of cron).
- why it matters: Cron/`--fingerprint` on large `self_monitor.log` → memory spike / slow; can fail review write path.
- suggested fix: Block-seek from EOF (read chunks backward) or `collections.deque(f, maxlen=n)`.

### [MEDIUM] `test_hysteresis_threshold` does not isolate hysteresis
- file: `tests/test_autonomy.py:84-97`
- what is wrong: Evidence sets `weeks_stable=1`, which already fails L0 requirement 「生產-like 穩定 ≥2 週」. Test only asserts `"複合分數" in failed`. Name/claim: composite alone refuses promotion.
- why it matters: Passes even if composite gate is deleted; weak regression net for R18 hysteresis.
- suggested fix: Use `weeks_stable=3` (and other L0 reqs met) with composite in `[0.85, 0.90)` only; assert sole/primary failure is 複合分數.

### [LOW] Dead / unused symbols
- file: `src/jarvis/clarify.py:41` (`CONFIDENCE_THRESHOLD` never referenced); `src/jarvis/autonomy.py:66` (`Operation.blast_radius` unused in `level()`)
- what is wrong: Documented signals not wired.
- why it matters: Readers assume confidence floor / blast radius affect gates; they do not.
- suggested fix: Wire them or delete + note in plan.

### [LOW] `_safest_option` assumes last option is safe for delete/send
- file: `src/jarvis/clarify.py:131-137`
- what is wrong: `return options[-1]` for delete/send with no validation that callers order escape-hatch last. Tests encode that convention (`["立即執行", "先計劃再執行"]`).
- why it matters: LLM-filled options in wrong order → “conservative” fallback picks the destructive reading.
- suggested fix: Prefer options matching deny keywords (唔/不/不要/等確認) or require explicit `safe_index` on `Unknown`.

---

## File-by-file (no-pad)

| File | Verdict |
|------|---------|
| `clarify.py` | 2 HIGH + 1 LOW (proceed / EVPI ask / dead threshold) |
| `eval_gate.py` | 1 MEDIUM (Windows encoding); suite hash / fail propagation OK |
| `prompt_pipeline.py` | 2 MEDIUM (scan vs introduce; format braces); PatternStore score gate OK |
| `autonomy.py` | 1 HIGH + 1 MEDIUM + 1 LOW (skip L1a; unused demote threshold; blast_radius) |
| `self_review.py` | 1 MEDIUM (full-file read); trend window logic OK |
| `asr_repair.py` early block | 1 HIGH (shellish bypass on token hit) |
| `tests/test_clarify.py` | OK for covered paths; **missing** tests for asked-unanswered proceed + impact-only ask |
| `tests/test_eval_gate.py` | OK |
| `tests/test_prompt_pipeline.py` | OK; no brace / introduce-diff cases |
| `tests/test_autonomy.py` | 1 MEDIUM (hysteresis isolation); promote target assert expects L1B — encodes the skip-L1a bug |
| `tests/test_self_review.py` | OK |
| `tests/test_brain.py` | Hermes `hermes_enabled=False` mocks look correct for local-brain paths |
| `tests/test_settings_ui_smoke.py` | 5 tabs match `settings_ui.py` (提醒/Hermes/系統/音訊診斷/進階) |

REVIEW DONE: 11 findings (C=0 H=4 M=5 L=2)

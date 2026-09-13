"""Durable alert queue (JSONL) for Hermes MCP peek/lease/ack.

Watcher enqueues short English phrases; Hermes polls via HTTP MCP.
State machine (pending/held/digest/spoken) is additive — peek stays
neutral (no gaming/voice gate).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

DEFAULT_MAX_DEPTH = 32
DEFAULT_TTL_S = 120.0
DEFAULT_LEASE_S = 30.0
READ_TIMEOUT_S = 1.0  # read paths; write paths keep _DirLock default 5s
HELD_CAP = 64
DEDUPE_WINDOW_S = 300.0
DIGEST_MAX_AGE_S = 24 * 3600.0
LEDGER_ROTATE_BYTES = 2 * 1024 * 1024
_VALID_STATES = frozenset({"pending", "held", "digest", "spoken"})
_VALID_PRIORITIES = frozenset({"normal", "critical"})

_log = logging.getLogger(__name__)
_ledger_warn_ts = 0.0
_lock_warn_ts = 0.0


def default_queue_path() -> Path:
    """``%APPDATA%\\Jarvis\\alerts\\queue.jsonl`` (Windows) or ``~/.jarvis/...``."""
    base = os.environ.get("APPDATA") or str(Path.home() / ".jarvis")
    return Path(base) / "Jarvis" / "alerts" / "queue.jsonl"


def default_store(
    path: Path | str | None = None, *, settings: Any | None = None
) -> AlertStore:
    """Production factory: injects priority policy + settings-driven caps (never raises)."""
    _policy = None
    try:
        try:
            from jarvis.alert_policy import priority_for as _policy
        except Exception:  # noqa: BLE001 — lazy import; fail-open
            _policy = None
        cfg = settings
        if cfg is None:
            try:
                from jarvis.settings import load_settings

                cfg = load_settings()
            except Exception:  # noqa: BLE001
                cfg = None
        kwargs: dict[str, Any] = {}
        if path is not None:
            kwargs["path"] = Path(path)
        if _policy is not None:
            kwargs["policy"] = _policy
        if cfg is not None:
            kwargs["held_cap"] = int(getattr(cfg, "alert_held_cap", HELD_CAP))
            kwargs["dedupe_window_s"] = float(
                getattr(cfg, "alert_dedupe_window_s", DEDUPE_WINDOW_S)
            )
            kwargs["digest_max_age_s"] = float(
                getattr(cfg, "alert_digest_ttl_s", DIGEST_MAX_AGE_S)
            )
        return AlertStore(**kwargs)
    except Exception:  # noqa: BLE001 — never raise from factory
        try:
            return AlertStore(Path(path) if path else None, policy=_policy)
        except Exception:  # noqa: BLE001
            return AlertStore()


def miss_ledger_path(queue_path: Path) -> Path:
    """Append-only miss ledger next to *queue_path*."""
    return Path(queue_path).parent / "miss_ledger.jsonl"


def read_miss_ledger(
    queue_path: Path | str | None = None,
    *,
    hours: float = 24.0,
    now: float | None = None,
) -> list[dict[str, Any]]:
    """Read miss ledger rows within *hours*; fail-open → ``[]``."""
    try:
        qp = Path(queue_path) if queue_path else default_queue_path()
        ledger = miss_ledger_path(qp)
        rotated = Path(str(ledger) + ".1")
        wall = time.time() if now is None else float(now)
        cutoff = wall - float(hours) * 3600.0
        upper = wall + 60.0
        dated: list[tuple[float, dict[str, Any]]] = []
        # .1 is older rotate; read both, sort by ts ascending.
        for path in (rotated, ledger):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(d, dict):
                    continue
                ts = d.get("ts")
                if not isinstance(ts, str):
                    continue
                try:
                    epoch = time.mktime(
                        time.strptime(ts, "%Y-%m-%dT%H:%M:%S")
                    )
                except (ValueError, OverflowError, OSError):
                    continue
                if cutoff <= epoch <= upper:
                    dated.append((epoch, d))
        dated.sort(key=lambda x: x[0])
        return [d for _, d in dated]
    except Exception:  # noqa: BLE001 — fail-open
        return []


def label_for(kind: str) -> str:
    """ASCII-safe short label for a kind ('' → 'alert').

    Known kinds use the digest display table; others share
    ``alert_policy.sanitize`` scrub (=, |, ->, <, >, quotes, URLs, non-ASCII)
    plus strip of 4+ digit runs (same regex as speakable gate).
    """
    from jarvis.alert_policy import _RE_DIGIT_RUN, sanitize

    k = str(kind or "").strip()
    known = {
        "whatsapp": "WhatsApp",
        "discord": "Discord",
        "cursor": "Cursor",
        "cursor_approve": "Cursor approval",
        "cursor_plan": "Cursor plan",
        "self-monitor": "self monitor",
        "gpu_health": "GPU health warning",
        "gpu_hard": "GPU critical alert",
        "extra": "notification",
        "test": "test alert",
    }
    if k in known:
        return known[k]
    label = sanitize(k)
    label = _RE_DIGIT_RUN.sub(" ", label)
    label = label.replace("_", " ").replace("-", " ")
    label = re.sub(r"\s+", " ", label).strip()[:40].strip()
    return label or "alert"


_label_for = label_for


def _count_clause(label: str, n: int) -> str:
    """'whatsapp x2'; counts over 999 read 'over 999' (no 'xover 999')."""
    return f"{label} x{n}" if n <= 999 else f"{label} over 999"


def format_missed_sentence(
    entries: list[dict[str, Any]], *, hours: float = 24.0
) -> str:
    """Deterministic ASCII English summary of unanswered alert ids."""
    _ = hours  # signature parity with read window; unused for phrasing
    if not entries:
        return "Sir, nothing missed."
    by_id: dict[str, list[dict[str, Any]]] = {}
    for i, e in enumerate(entries):
        key = str(e.get("id") or "").strip() or f"__row{i}"
        by_id.setdefault(key, []).append(e)

    def _answered(rows: list[dict[str, Any]]) -> bool:
        return any(
            str(row.get("event") or "").lower() == "spoken" for row in rows
        )

    unanswered = [rows for rows in by_id.values() if not _answered(rows)]
    total = len(unanswered)
    if total == 0:
        return "Sir, nothing missed."

    from jarvis.alert_policy import _fmt_count

    counts: dict[str, int] = {}
    for rows in unanswered:
        label = _label_for(str(rows[0].get("kind") or ""))
        counts[label] = counts.get(label, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    parts = [_count_clause(label, n) for label, n in ranked[:3]]
    clause = ", ".join(parts)
    if len(ranked) > 3:
        clause = clause + " and others"
    sentence = (
        f"Sir, {_fmt_count(total)} alert{'s' if total != 1 else ''} "
        f"went unanswered while you were away: {clause}."
    )
    try:
        from jarvis.alert_policy import is_speakable
    except Exception:  # noqa: BLE001
        return (
            sentence
            if sentence.isascii()
            else "Sir, some alerts went unanswered while you were away."
        )
    if not is_speakable(sentence):
        return "Sir, some alerts went unanswered while you were away."
    return sentence


@dataclass
class StoredAlert:
    """One queue row."""

    id: str
    kind: str
    phrase: str
    app: str = ""
    detail: str = ""
    ts: float = 0.0
    ttl_s: float = DEFAULT_TTL_S
    status: str = "pending"  # pending | leased | acked (lease machinery)
    lease_until: float = 0.0
    state: str = "pending"  # pending | held | digest | spoken
    hold_until: float = 0.0
    priority: str = "normal"  # normal | critical
    dedupe_key: str = ""
    digest_at: float = 0.0

    def expired(self, now: float | None = None) -> bool:
        """TTL check. Held/digest never expire via this helper (GC transitions them)."""
        if self.state in ("held", "digest"):
            return False
        t = time.time() if now is None else now
        return (t - float(self.ts)) > float(self.ttl_s)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StoredAlert:
        raw = str(d.get("state") or "pending")
        state = raw
        if state not in _VALID_STATES:
            _log.warning(
                "[warn] alert_store unknown state %r → pending", raw
            )
            state = "pending"
        priority = str(d.get("priority") or "normal")
        if priority not in _VALID_PRIORITIES:
            priority = "normal"
        return cls(
            id=str(d.get("id") or ""),
            kind=str(d.get("kind") or ""),
            phrase=str(d.get("phrase") or ""),
            app=str(d.get("app") or ""),
            detail=str(d.get("detail") or ""),
            ts=float(d.get("ts") or 0.0),
            ttl_s=float(d.get("ttl_s") or DEFAULT_TTL_S),
            status=str(d.get("status") or "pending"),
            lease_until=float(d.get("lease_until") or 0.0),
            state=state,
            hold_until=float(d.get("hold_until") or 0.0),
            priority=priority,
            dedupe_key=str(d.get("dedupe_key") or ""),
            digest_at=float(d.get("digest_at") or 0.0),
        )


class _DirLock:
    """Cross-process lock via atomic mkdir (works on Windows)."""

    def __init__(
        self,
        path: Path,
        timeout_s: float = 5.0,
        stale_s: float = 30.0,
    ) -> None:
        self._path = path
        self._timeout_s = float(timeout_s)
        self._stale_s = float(stale_s)
        self._held = False

    def __enter__(self) -> _DirLock:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + self._timeout_s
        while True:
            try:
                self._path.mkdir(exist_ok=False)
                self._held = True
                return self
            except FileExistsError:
                if time.time() > deadline:
                    raise TimeoutError(str(self._path)) from None
                try:
                    age = time.time() - self._path.stat().st_mtime
                    if age > self._stale_s:
                        try:
                            self._path.rmdir()
                        except OSError:
                            pass
                except OSError:
                    pass
                time.sleep(0.02)

    def __exit__(self, *exc: object) -> None:
        if self._held:
            try:
                self._path.rmdir()
            except OSError:
                pass
            self._held = False


class AlertStore:
    """JSONL store with peek/lease/ack + hold/digest/spoken transitions."""

    def __init__(
        self,
        path: Path | None = None,
        *,
        max_depth: int = DEFAULT_MAX_DEPTH,
        default_ttl_s: float = DEFAULT_TTL_S,
        default_lease_s: float = DEFAULT_LEASE_S,
        policy: Callable[[str], str] | None = None,
        held_cap: int = HELD_CAP,
        dedupe_window_s: float = DEDUPE_WINDOW_S,
        digest_max_age_s: float = DIGEST_MAX_AGE_S,
        digest_cap: int | None = None,
    ) -> None:
        self.path = Path(path) if path else default_queue_path()
        self.max_depth = max(1, int(max_depth))
        self.default_ttl_s = float(default_ttl_s)
        self.default_lease_s = float(default_lease_s)
        self._policy = policy
        self.held_cap = int(held_cap)
        self.dedupe_window_s = float(dedupe_window_s)
        self.digest_max_age_s = float(digest_max_age_s)
        # ponytail: digest_cap defaults to max(64, held_cap*2); override via ctor.
        self.digest_cap = (
            int(digest_cap)
            if digest_cap is not None
            else max(64, self.held_cap * 2)
        )
        self._lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self._ledger_path = miss_ledger_path(self.path)

    def _warn_lock_timeout(self) -> None:
        global _lock_warn_ts
        wall = time.time()
        if wall - _lock_warn_ts >= 60.0:
            _lock_warn_ts = wall
            _log.warning("[warn] alert_store lock timeout: %s", self._lock_path)

    def enqueue(
        self,
        *,
        kind: str,
        phrase: str,
        app: str = "",
        detail: str = "",
        ttl_s: float | None = None,
        dedupe_key: str = "",
        priority: str | None = None,
    ) -> StoredAlert:
        """Append one pending alert; drop oldest pending-normal if over max_depth.

        On dedupe hit, returns the **existing** persisted row (same id).
        """
        kind_s = str(kind or "").strip() or "unknown"
        pri = str(priority or "").strip()
        if pri not in _VALID_PRIORITIES:
            if self._policy is not None:
                value: Any
                try:
                    value = self._policy(kind_s)
                except Exception as exc:  # noqa: BLE001 — fail-safe to critical
                    value = exc
                    pri = ""
                else:
                    pri = str(value or "")
                if pri not in _VALID_PRIORITIES:
                    _log.warning(
                        "alert_store: illegal policy result %r for kind=%r — using 'critical'",
                        value,
                        kind_s,
                    )
                    pri = "critical"
            else:
                pri = "normal"
        row = StoredAlert(
            id=uuid.uuid4().hex,
            kind=kind_s,
            phrase=str(phrase or "").strip(),
            app=str(app or "").strip(),
            detail=str(detail or "").strip(),
            ts=time.time(),
            ttl_s=float(ttl_s if ttl_s is not None else self.default_ttl_s),
            status="pending",
            lease_until=0.0,
            state="pending",
            hold_until=0.0,
            priority=pri,
            dedupe_key=str(dedupe_key or ""),
        )
        if not row.phrase:
            raise ValueError("phrase required")
        with _DirLock(self._lock_path):
            rows = self._gc_unlocked(self._load_unlocked())
            # dedupe: drop new if same kind+dedupe_key within window
            if row.dedupe_key:
                cutoff = row.ts - self.dedupe_window_s
                for existing in rows:
                    if (
                        existing.kind == row.kind
                        and existing.dedupe_key == row.dedupe_key
                        and float(existing.ts) >= cutoff
                    ):
                        self._ledger(
                            existing.id,
                            existing.kind,
                            "enqueue",
                            "dedupe",
                            now=row.ts,
                        )
                        self._save_unlocked(rows)
                        return existing
            rows.append(row)
            self._ledger(row.id, row.kind, "enqueue", "ok", now=row.ts)
            # ponytail: eviction stops when no eligible victim — queue may
            # temporarily exceed max_depth so _DirLock hold stays bounded.
            while self._depth_count(rows) > self.max_depth:
                victim = None
                for i, r in enumerate(rows):
                    if (
                        r.state == "pending"
                        and r.priority == "normal"
                        and float(r.ts) < float(row.ts)
                    ):
                        victim = i
                        break
                if victim is None:
                    break
                dropped = rows.pop(victim)
                self._ledger(dropped.id, dropped.kind, "drop", "evict", now=row.ts)
            self._save_unlocked(rows)
        return row

    def peek(self, *, lease_s: float | None = None) -> StoredAlert | None:
        """Lease oldest state==pending row (or expired-lease). Neutral — no gate."""
        lease = float(lease_s if lease_s is not None else self.default_lease_s)
        now = time.time()
        try:
            with _DirLock(self._lock_path, timeout_s=READ_TIMEOUT_S):
                # persist=False: no GC filter — save full list (lease fields only).
                rows = self._gc_unlocked(self._load_unlocked(), now=now, persist=False)
                for r in rows:
                    if r.state != "pending":
                        continue
                    if self._would_expire(r, now):
                        continue
                    if r.status == "acked":
                        continue
                    if r.status == "leased" and r.lease_until > now:
                        continue
                    # pending or lease expired → redeliver
                    r.status = "leased"
                    r.lease_until = now + max(0.05, lease)
                    self._save_unlocked(rows)
                    return r
                return None
        except TimeoutError:
            self._warn_lock_timeout()
            return None

    def ack(self, alert_id: str) -> bool:
        """Mark leased/pending id as acked. Returns False if missing."""
        aid = str(alert_id or "").strip()
        if not aid:
            return False
        with _DirLock(self._lock_path):
            rows = self._gc_unlocked(self._load_unlocked())
            found = False
            for r in rows:
                if r.id == aid:
                    r.status = "acked"
                    r.lease_until = 0.0
                    found = True
                    break
            # drop acked from file (keep store small)
            rows = [r for r in rows if r.status != "acked"]
            self._save_unlocked(rows)
            return found

    def hold(
        self,
        ids: list[str],
        ttl_s: float,
        now: float | None = None,
    ) -> int:
        """pending → held; release lease. Returns count transitioned."""
        t = time.time() if now is None else float(now)
        want = {str(i) for i in (ids or []) if str(i)}
        if not want:
            return 0
        ttl = max(0.0, float(ttl_s))
        with _DirLock(self._lock_path):
            rows = self._gc_unlocked(self._load_unlocked(), now=t)
            n = 0
            for r in rows:
                if r.id in want and r.state == "pending":
                    r.state = "held"
                    r.hold_until = t + ttl
                    r.lease_until = 0.0
                    r.status = "pending"
                    self._ledger(r.id, r.kind, "hold", "ok", now=t)
                    n += 1
            self._enforce_held_cap(rows, now=t)
            self._save_unlocked(rows)
            return n

    def release_held(
        self, ids: list[str] | None = None, now: float | None = None
    ) -> int:
        """held → pending (leave hold_until for audit); refresh ts so TTL restarts.

        ``ids=None`` releases all held; ``ids=[...]`` releases only those ids.
        No-op (no file write) when nothing transitions.
        """
        t = time.time() if now is None else float(now)
        want = None if ids is None else {str(i) for i in ids if str(i)}
        with _DirLock(self._lock_path):
            rows = self._load_unlocked()
            n = 0
            for r in rows:
                if r.state != "held":
                    continue
                if want is not None and r.id not in want:
                    continue
                r.state = "pending"
                r.status = "pending"
                r.lease_until = 0.0
                r.ts = t
                self._ledger(r.id, r.kind, "release", "ok", now=t)
                n += 1
            if n == 0:
                return 0
            self._save_unlocked(self._gc_unlocked(rows, now=t))
            return n

    def held_rows(self, now: float | None = None) -> list[StoredAlert]:
        """Return current held-state rows (read-only; excludes would-expire)."""
        t = time.time() if now is None else float(now)
        try:
            with _DirLock(self._lock_path, timeout_s=READ_TIMEOUT_S):
                rows = self._gc_unlocked(self._load_unlocked(), now=t, persist=False)
                return [
                    r
                    for r in rows
                    if r.state == "held" and not self._would_expire(r, t)
                ]
        except TimeoutError:
            self._warn_lock_timeout()
            return []

    def gc(self, now: float | None = None, *, persist: bool = True) -> None:
        """Write-path GC only (expiry drops + hold_timeout→digest). No held release.

        Skip ``_save_unlocked`` when serialized rows are unchanged (no SSD churn).
        ``persist=False`` never writes (escape hatch).
        """
        t = time.time() if now is None else float(now)
        with _DirLock(self._lock_path):
            rows_before = self._load_unlocked()
            before = [r.to_dict() for r in rows_before]
            rows = self._gc_unlocked(rows_before, now=t)
            after = [r.to_dict() for r in rows]
            if not persist or before == after:
                return
            self._save_unlocked(rows)

    def mark_spoken(self, ids: list[str], now: float | None = None) -> int:
        """→ spoken claim (ledger event ``speak_claim``; real ``spoken`` after TTS)."""
        return self._set_state(ids, "spoken", "speak_claim", reason="ok", now=now)

    def mark_digest(self, ids: list[str], now: float | None = None) -> int:
        """→ digest."""
        return self._set_state(ids, "digest", "digest", reason="ok", now=now)

    def drop(self, ids: list[str], reason: str, now: float | None = None) -> int:
        """Remove rows + ledger entry with reason."""
        t = time.time() if now is None else float(now)
        want = {str(i) for i in (ids or []) if str(i)}
        if not want:
            return 0
        with _DirLock(self._lock_path):
            rows = self._gc_unlocked(self._load_unlocked(), now=t)
            kept: list[StoredAlert] = []
            n = 0
            for r in rows:
                if r.id in want:
                    self._ledger(r.id, r.kind, "drop", str(reason or ""), now=t)
                    n += 1
                else:
                    kept.append(r)
            self._save_unlocked(kept)
            return n

    def digest_rows(self, now: float | None = None) -> list[StoredAlert]:
        """Return current digest-state rows (read-only; excludes would-expire)."""
        t = time.time() if now is None else float(now)
        try:
            with _DirLock(self._lock_path, timeout_s=READ_TIMEOUT_S):
                rows = self._gc_unlocked(self._load_unlocked(), now=t, persist=False)
                return [
                    r
                    for r in rows
                    if r.state == "digest" and not self._would_expire(r, t)
                ]
        except TimeoutError:
            self._warn_lock_timeout()
            return []

    def clear_digest(self, ids: list[str], now: float | None = None) -> int:
        """Remove rows by id after digest was spoken (ack-style; any state)."""
        t = time.time() if now is None else float(now)
        want = {str(i) for i in (ids or []) if str(i)}
        if not want:
            return 0
        with _DirLock(self._lock_path):
            rows = self._gc_unlocked(self._load_unlocked(), now=t)
            kept: list[StoredAlert] = []
            n = 0
            for r in rows:
                if r.id in want:
                    self._ledger(r.id, r.kind, "clear_digest", "clear_digest", now=t)
                    n += 1
                else:
                    kept.append(r)
            self._save_unlocked(kept)
            return n

    def list_open(self) -> list[StoredAlert]:
        """Speakable open rows only (state==pending); held/digest excluded."""
        t = time.time()
        try:
            with _DirLock(self._lock_path, timeout_s=READ_TIMEOUT_S):
                rows = self._gc_unlocked(self._load_unlocked(), now=t, persist=False)
                return [
                    r
                    for r in rows
                    if r.state == "pending"
                    and r.status != "acked"
                    and not self._would_expire(r, t)
                ]
        except TimeoutError:
            self._warn_lock_timeout()
            return []

    def stats(self) -> dict[str, Any]:
        """Counts. Old keys (open/pending/leased) map to state==pending subset."""
        now = time.time()
        dropped_24h = 0
        try:
            dropped_24h = sum(
                1
                for e in read_miss_ledger(self.path, hours=24.0, now=now)
                if e.get("event") == "drop"
            )
        except Exception:  # noqa: BLE001 — fail-open
            dropped_24h = 0
        empty = {
            "path": str(self.path),
            "open": 0,
            "pending": 0,
            "leased": 0,
            "max_depth": self.max_depth,
            "states": {"pending": 0, "held": 0, "digest": 0, "spoken": 0},
            "dropped_24h": dropped_24h,
        }
        try:
            with _DirLock(self._lock_path, timeout_s=READ_TIMEOUT_S):
                rows = self._gc_unlocked(self._load_unlocked(), now=now, persist=False)
        except TimeoutError:
            self._warn_lock_timeout()
            return empty
        visible = [r for r in rows if not self._would_expire(r, now)]
        states = {"pending": 0, "held": 0, "digest": 0, "spoken": 0}
        for r in visible:
            if r.state in states:
                states[r.state] += 1
        pending_rows = [
            r for r in visible if r.state == "pending" and r.status != "acked"
        ]
        leased = pending = 0
        for r in pending_rows:
            if r.status == "leased" and r.lease_until > now:
                leased += 1
            else:
                pending += 1
        return {
            "path": str(self.path),
            "open": len(pending_rows),
            "pending": pending,
            "leased": leased,
            "max_depth": self.max_depth,
            "states": states,
            "dropped_24h": dropped_24h,
        }

    def _set_state(
        self,
        ids: list[str],
        new_state: str,
        event: str,
        *,
        reason: str = "ok",
        now: float | None = None,
    ) -> int:
        t = time.time() if now is None else float(now)
        want = {str(i) for i in (ids or []) if str(i)}
        if not want:
            return 0
        with _DirLock(self._lock_path):
            rows = self._gc_unlocked(self._load_unlocked(), now=t)
            n = 0
            for r in rows:
                if r.id in want:
                    r.state = new_state
                    r.lease_until = 0.0
                    if new_state == "digest":
                        r.digest_at = t
                    if new_state == "spoken":
                        # Refresh ts so GC won't drop as spoken_expired mid-TTS
                        # (same pattern as release_held).
                        r.ts = t
                    self._ledger(r.id, r.kind, event, reason, now=t)
                    n += 1
            if new_state == "digest":
                self._enforce_digest_cap(rows, now=t)
            self._save_unlocked(rows)
            return n

    def _enforce_held_cap(self, rows: list[StoredAlert], *, now: float) -> None:
        # ponytail: collapse/demote loops terminate when no eligible victim —
        # held count may temporarily exceed held_cap so lock hold stays bounded.
        while True:
            # critical held rows do not count toward held_cap
            held = [
                r
                for r in rows
                if r.state == "held" and r.priority != "critical"
            ]
            if len(held) <= self.held_cap:
                self._enforce_digest_cap(rows, now=now)
                return
            # collapse same kind+app (keep newest); critical never collapse victims
            groups: dict[tuple[str, str], list[StoredAlert]] = {}
            for r in held:
                groups.setdefault((r.kind, r.app), []).append(r)
            collapsed = False
            for group in groups.values():
                if len(group) <= 1:
                    continue
                group.sort(key=lambda x: float(x.ts), reverse=True)
                for old in group[1:]:
                    old.state = "digest"
                    old.digest_at = now
                    self._ledger(old.id, old.kind, "digest", "collapse", now=now)
                    collapsed = True
                break  # one group per pass, then re-check count
            if collapsed:
                continue
            # still over: demote oldest held normal → digest
            normals = [r for r in held if r.priority == "normal"]
            if not normals:
                self._enforce_digest_cap(rows, now=now)
                return
            oldest = min(normals, key=lambda x: float(x.ts))
            oldest.state = "digest"
            oldest.digest_at = now
            self._ledger(oldest.id, oldest.kind, "digest", "held_cap", now=now)

    def _enforce_digest_cap(self, rows: list[StoredAlert], *, now: float) -> None:
        """Drop oldest digest rows when over digest_cap (ledger drop/digest_cap)."""
        while True:
            digests = [r for r in rows if r.state == "digest"]
            if len(digests) <= self.digest_cap:
                return
            oldest = min(
                digests,
                key=lambda x: (
                    float(x.digest_at) if float(x.digest_at) > 0.0 else float(x.ts),
                    float(x.ts),
                ),
            )
            rows.remove(oldest)
            self._ledger(oldest.id, oldest.kind, "drop", "digest_cap", now=now)

    @staticmethod
    def _depth_count(rows: list[StoredAlert]) -> int:
        return sum(1 for r in rows if r.status != "acked")

    def _would_expire(self, r: StoredAlert, t: float) -> bool:
        """True iff persist=True GC would drop or hold_timeout→digest this row."""
        if r.status == "acked":
            return True
        if r.state == "held" and float(r.hold_until) > 0.0 and t >= float(r.hold_until):
            return True  # would become digest — not showable as held
        if r.state == "held":
            return False
        if r.state == "digest":
            age_base = float(r.digest_at) if float(r.digest_at) > 0.0 else float(r.ts)
            return (t - age_base) > self.digest_max_age_s
        if r.state == "spoken":
            return (t - float(r.ts)) > self.default_ttl_s
        # pending
        return bool(r.expired(t))

    def _gc_unlocked(
        self,
        rows: list[StoredAlert],
        *,
        now: float | None = None,
        persist: bool = True,
    ) -> list[StoredAlert]:
        # persist=False: pure no-op — no filter, no ledger, same objects/order.
        if not persist:
            return rows
        t = time.time() if now is None else float(now)
        out: list[StoredAlert] = []
        for r in rows:
            if r.status == "acked":
                continue
            # held past hold_until → digest (not deleted)
            if r.state == "held" and float(r.hold_until) > 0.0 and t >= float(r.hold_until):
                r.state = "digest"
                r.digest_at = t
                self._ledger(r.id, r.kind, "digest", "hold_timeout", now=t)
            if r.state == "held":
                out.append(r)
                continue
            if r.state == "digest":
                age_base = float(r.digest_at) if float(r.digest_at) > 0.0 else float(r.ts)
                if (t - age_base) > self.digest_max_age_s:
                    self._ledger(r.id, r.kind, "drop", "digest_expired", now=t)
                    continue
                out.append(r)
                continue
            if r.state == "spoken":
                if (t - float(r.ts)) > self.default_ttl_s:
                    self._ledger(r.id, r.kind, "drop", "spoken_expired", now=t)
                    continue
                out.append(r)
                continue
            # pending
            if r.expired(t):
                self._ledger(r.id, r.kind, "drop", "ttl_expired", now=t)
                continue
            out.append(r)
        self._enforce_digest_cap(out, now=t)
        return out

    def _ledger(
        self,
        alert_id: str,
        kind: str,
        event: str,
        reason: str,
        *,
        now: float | None = None,
    ) -> None:
        """Append-only miss ledger; fail-open (never raise into caller)."""
        global _ledger_warn_ts
        try:
            path = self._ledger_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.is_file() and path.stat().st_size > LEDGER_ROTATE_BYTES:
                rotated = path.with_suffix(path.suffix + ".1")
                try:
                    if rotated.exists():
                        rotated.unlink()
                    path.replace(rotated)
                except OSError:
                    pass
            t = time.time() if now is None else float(now)
            line = json.dumps(
                {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t)),
                    "id": alert_id,
                    "kind": kind,
                    "event": event,
                    "reason": reason,
                },
                ensure_ascii=False,
            )
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as exc:  # noqa: BLE001 — fail-open
            wall = time.time()
            if wall - _ledger_warn_ts >= 60.0:
                _ledger_warn_ts = wall
                _log.warning("[warn] miss_ledger write failed: %s", exc)

    def _load_unlocked(self) -> list[StoredAlert]:
        if not self.path.is_file():
            return []
        out: list[StoredAlert] = []
        try:
            text = self.path.read_text(encoding="utf-8")
        except OSError:
            return []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(d, dict) and d.get("id"):
                out.append(StoredAlert.from_dict(d))
        return out

    def _save_unlocked(self, rows: list[StoredAlert]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(f"{self.path.name}.{os.getpid()}.tmp")
        body = "\n".join(json.dumps(r.to_dict(), ensure_ascii=False) for r in rows)
        if body:
            body += "\n"
        try:
            tmp.write_text(body, encoding="utf-8")
            os.replace(tmp, self.path)
        except Exception:
            try:
                tmp.unlink(missing_ok=True)  # type: ignore[call-arg]
            except TypeError:
                try:
                    if tmp.exists():
                        tmp.unlink()
                except OSError:
                    pass
            except OSError:
                pass
            raise

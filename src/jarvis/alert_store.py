"""Durable alert queue (JSONL) for Hermes MCP peek/lease/ack.

Watcher enqueues short English phrases; Hermes polls via HTTP MCP.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

DEFAULT_MAX_DEPTH = 32
DEFAULT_TTL_S = 120.0
DEFAULT_LEASE_S = 30.0


def default_queue_path() -> Path:
    """``%APPDATA%\\Jarvis\\alerts\\queue.jsonl`` (Windows) or ``~/.jarvis/...``."""
    base = os.environ.get("APPDATA") or str(Path.home() / ".jarvis")
    return Path(base) / "Jarvis" / "alerts" / "queue.jsonl"


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
    status: str = "pending"  # pending | leased | acked
    lease_until: float = 0.0

    def expired(self, now: float | None = None) -> bool:
        t = time.time() if now is None else now
        return (t - float(self.ts)) > float(self.ttl_s)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StoredAlert:
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
        )


class _DirLock:
    """Cross-process lock via atomic mkdir (works on Windows)."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._held = False

    def __enter__(self) -> _DirLock:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + 10.0
        while True:
            try:
                self._path.mkdir(exist_ok=False)
                self._held = True
                return self
            except FileExistsError:
                if time.time() > deadline:
                    # stale lock: take over after timeout
                    try:
                        self._path.rmdir()
                    except OSError:
                        pass
                    continue
                time.sleep(0.02)

    def __exit__(self, *exc: object) -> None:
        if self._held:
            try:
                self._path.rmdir()
            except OSError:
                pass
            self._held = False


class AlertStore:
    """JSONL store with peek/lease/ack. Max depth drops oldest open rows."""

    def __init__(
        self,
        path: Path | None = None,
        *,
        max_depth: int = DEFAULT_MAX_DEPTH,
        default_ttl_s: float = DEFAULT_TTL_S,
        default_lease_s: float = DEFAULT_LEASE_S,
    ) -> None:
        self.path = Path(path) if path else default_queue_path()
        self.max_depth = max(1, int(max_depth))
        self.default_ttl_s = float(default_ttl_s)
        self.default_lease_s = float(default_lease_s)
        self._lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def enqueue(
        self,
        *,
        kind: str,
        phrase: str,
        app: str = "",
        detail: str = "",
        ttl_s: float | None = None,
    ) -> StoredAlert:
        """Append one pending alert; drop oldest if over max_depth."""
        row = StoredAlert(
            id=uuid.uuid4().hex,
            kind=str(kind or "").strip() or "unknown",
            phrase=str(phrase or "").strip(),
            app=str(app or "").strip(),
            detail=str(detail or "").strip(),
            ts=time.time(),
            ttl_s=float(ttl_s if ttl_s is not None else self.default_ttl_s),
            status="pending",
            lease_until=0.0,
        )
        if not row.phrase:
            raise ValueError("phrase required")
        with _DirLock(self._lock_path):
            rows = self._load_unlocked()
            rows = self._gc_unlocked(rows)
            rows.append(row)
            while len([r for r in rows if r.status != "acked"]) > self.max_depth:
                # drop oldest non-acked
                for i, r in enumerate(rows):
                    if r.status != "acked":
                        del rows[i]
                        break
                else:
                    break
            self._save_unlocked(rows)
        return row

    def peek(self, *, lease_s: float | None = None) -> StoredAlert | None:
        """Lease oldest pending (or expired-lease) row."""
        lease = float(lease_s if lease_s is not None else self.default_lease_s)
        now = time.time()
        with _DirLock(self._lock_path):
            rows = self._gc_unlocked(self._load_unlocked())
            for r in rows:
                if r.status == "acked":
                    continue
                if r.status == "leased" and r.lease_until > now:
                    continue
                # pending or lease expired → redeliver
                r.status = "leased"
                r.lease_until = now + max(0.05, lease)
                self._save_unlocked(rows)
                return r
            self._save_unlocked(rows)
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

    def list_open(self) -> list[StoredAlert]:
        """Non-acked rows after GC (leases left as-is)."""
        with _DirLock(self._lock_path):
            rows = self._gc_unlocked(self._load_unlocked())
            self._save_unlocked(rows)
            return [r for r in rows if r.status != "acked"]

    def stats(self) -> dict[str, Any]:
        """Counts for open rows."""
        now = time.time()
        open_rows = self.list_open()
        pending = leased = 0
        for r in open_rows:
            if r.status == "leased" and r.lease_until > now:
                leased += 1
            else:
                pending += 1
        return {
            "path": str(self.path),
            "open": len(open_rows),
            "pending": pending,
            "leased": leased,
            "max_depth": self.max_depth,
        }

    def _gc_unlocked(self, rows: list[StoredAlert]) -> list[StoredAlert]:
        now = time.time()
        out: list[StoredAlert] = []
        for r in rows:
            if r.status == "acked":
                continue
            if r.expired(now):
                continue
            out.append(r)
        return out

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
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        body = "\n".join(json.dumps(r.to_dict(), ensure_ascii=False) for r in rows)
        if body:
            body += "\n"
        tmp.write_text(body, encoding="utf-8")
        tmp.replace(self.path)

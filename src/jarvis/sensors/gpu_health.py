"""RTX 50-aware GPU health policy → short alert phrases.

Primary signals: core temp + sustained clock drop under load.
Ignores 255°C-class garbage. Unofficial hotspot is out of scope for P0.

Dynamic calibration: soft clock alerts only after a load baseline is learned.
Hard temp ceiling always fires (even before calibration).
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field

from jarvis.sensors.backend import GpuSnapshot

_log = logging.getLogger("jarvis.sensors.gpu_health")


def gpu_health_phrase(reason: str) -> str:
    """English stub for Hermes TTS."""
    r = (reason or "").strip().lower()
    if r == "clock_drop":
        return "GPU health warning. Clocks dropped under load."
    if r == "hot":
        return "GPU thermal stress."
    if r == "mem_hot":
        return "GPU memory temperature is high."
    return "GPU health warning."


@dataclass(frozen=True)
class GpuHealthHit:
    """Alert payload without importing AlertWatcher (avoid cycles)."""

    kind: str
    phrase: str
    detail: str


@dataclass
class _Sample:
    t: float
    temp_c: float | None
    mem_temp_c: float | None
    util_pct: float | None
    clock_mhz: float | None


@dataclass
class GpuHealthMonitor:
    """Stateful evaluator: dynamic baseline + hard ceiling + per-reason cooldown."""

    history: int = 12
    util_load_pct: float = 60.0
    clock_drop_ratio: float = 0.85
    clock_drop_hits: int = 2
    soft_temp_c: float = 83.0
    hard_temp_c: float = 90.0
    mem_temp_warn_c: float = 95.0
    soft_cooldown_s: float = 120.0
    hard_cooldown_s: float = 0.0
    calibrate_loaded_samples: int = 6
    _hist: deque[_Sample] = field(default_factory=deque, init=False, repr=False)
    _drop_streak: int = field(default=0, init=False, repr=False)
    _last_emit: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _calibrated: bool = field(default=False, init=False, repr=False)
    _peak_clock: float | None = field(default=None, init=False, repr=False)
    _was_ok: bool = field(default=True, init=False, repr=False)
    _on_log: object | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        maxlen = max(4, int(self.history))
        object.__setattr__(self, "_hist", deque(maxlen=maxlen))

    def set_log(self, fn) -> None:  # noqa: ANN001
        """Optional ``fn(str)`` for transition warnings (AlertWatcher)."""
        self._on_log = fn

    def _log(self, msg: str) -> None:
        _log.warning("%s", msg)
        if self._on_log is not None:
            try:
                self._on_log(msg)  # type: ignore[operator]
            except Exception:
                pass

    def evaluate(self, snap: GpuSnapshot) -> GpuHealthHit | None:
        """Return alert hit or None."""
        if not snap.ok:
            if self._was_ok:
                self._log(f"[warn] GPU sensor gap — clearing hist ({snap.error or 'ok=False'})")
            self._clear_state()
            self._was_ok = False
            return None
        if not self._was_ok:
            self._log("[ok] GPU sensor recovered")
        self._was_ok = True

        now = time.monotonic()
        self._hist.append(
            _Sample(
                t=now,
                temp_c=snap.temp_c,
                mem_temp_c=snap.mem_temp_c,
                util_pct=snap.util_pct,
                clock_mhz=snap.clock_mhz,
            )
        )
        self._update_calibration()

        reason, hard = self._reason()
        if not reason:
            return None
        cd = self.hard_cooldown_s if hard else self.soft_cooldown_s
        last = self._last_emit.get(reason)
        # None = never emitted: a first emit must NOT be blocked by a cooldown
        # (a 0.0 sentinel would mis-block when boot uptime < cooldown_s).
        if last is not None and cd > 0 and now - last < cd:
            return None
        self._last_emit[reason] = now
        phrase = gpu_health_phrase(reason)
        detail = (
            f"temp={snap.temp_c} mem={snap.mem_temp_c} "
            f"util={snap.util_pct} clock={snap.clock_mhz} "
            f"reason={reason} hard={hard} calib={self._calibrated} "
            f"src={snap.source}"
        )
        return GpuHealthHit(kind="gpu_health", phrase=phrase, detail=detail)

    def _clear_state(self) -> None:
        self._hist.clear()
        self._drop_streak = 0
        # Keep calibration + emit cooldowns across brief gaps? eng D7': clear hist/streak.
        # Re-learn peak after gap to avoid stale high peak → false soft silence.
        self._calibrated = False
        self._peak_clock = None

    def _update_calibration(self) -> None:
        if self._calibrated:
            # Still track peak under load for soft clock
            loaded = [
                s.clock_mhz
                for s in self._hist
                if s.clock_mhz is not None
                and s.util_pct is not None
                and s.util_pct >= self.util_load_pct
            ]
            if loaded:
                peak = max(loaded)
                if self._peak_clock is None or peak > self._peak_clock:
                    self._peak_clock = peak
            return
        loaded = [
            s.clock_mhz
            for s in self._hist
            if s.clock_mhz is not None
            and s.util_pct is not None
            and s.util_pct >= self.util_load_pct
        ]
        need = max(3, int(self.calibrate_loaded_samples))
        if len(loaded) < need:
            return
        self._peak_clock = max(loaded)
        self._calibrated = True
        self._log(
            f"[ok] GPU health calibrated peak_clock={self._peak_clock:.0f} MHz "
            f"(n={len(loaded)})"
        )

    def _reason(self) -> tuple[str | None, bool]:
        """Return (reason, is_hard)."""
        if not self._hist:
            return None, False
        cur = self._hist[-1]

        # Hard ceiling — always, even before calibration
        if cur.temp_c is not None and cur.temp_c >= self.hard_temp_c:
            return "hot", True
        if cur.mem_temp_c is not None and cur.mem_temp_c >= self.mem_temp_warn_c:
            # mem high treated as hard-ish (short cooldown)
            return "mem_hot", True

        # Soft temp only after calibrated (avoid idle false / pre-baseline noise)
        if (
            self._calibrated
            and cur.temp_c is not None
            and cur.temp_c >= self.soft_temp_c
        ):
            return "hot", False

        # Soft clock-drop under load — only after baseline peak known
        if not self._calibrated or self._peak_clock is None or self._peak_clock <= 0:
            self._drop_streak = 0
            return None, False
        if (
            cur.util_pct is None
            or cur.clock_mhz is None
            or cur.util_pct < self.util_load_pct
        ):
            self._drop_streak = 0
            return None, False
        if cur.clock_mhz < self._peak_clock * self.clock_drop_ratio:
            self._drop_streak += 1
        else:
            self._drop_streak = 0
        if self._drop_streak >= max(1, int(self.clock_drop_hits)):
            self._drop_streak = 0
            return "clock_drop", False
        return None, False

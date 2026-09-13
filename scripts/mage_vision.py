"""CLI test for Mage-VL image understanding (no voice).

Usage: python scripts/mage_vision.py <image_path> [prompt]
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/mage_vision.py <image_path> [prompt]",
            file=sys.stderr,
        )
        return 1

    image_path = sys.argv[1]
    prompt = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "Describe this image in detail."
    )

    from jarvis.mage_engine import MageVLEngine

    engine = MageVLEngine()
    load_s = engine.warm()
    if load_s:
        print(f"[load] {load_s:.2f}s", file=sys.stderr)
    answer = engine.understand_image(image_path, prompt=prompt)
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

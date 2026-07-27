"""CLI entry: python -m jarvis -c \"open CS2\" | serve | autostart | listen"""

from __future__ import annotations

import argparse
import sys

from jarvis.engine import execute_utterance


def _ask_yes(prompt: str) -> bool:
    try:
        ans = input(prompt).strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes", "是", "係", "ok")


def run_utterance(text: str, *, dry_run: bool = False) -> int:
    """CLI wrapper around execute_utterance."""
    result = execute_utterance(text, dry_run=dry_run, ask_confirm=_ask_yes)
    for line in result.lines:
        print(line)
    return 0 if result.ok else 1


def main(argv: list[str] | None = None) -> None:
    """Parse CLI args and run one command or the shell."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    raw = list(sys.argv[1:] if argv is None else argv)
    if raw and raw[0] == "serve":
        from jarvis.shell_app import run_shell

        run_shell()
        raise SystemExit(0)

    if raw and raw[0] == "autostart":
        from jarvis import autostart as auto

        sub = raw[1] if len(raw) > 1 else "status"
        if sub == "on":
            print(auto.enable())
        elif sub == "off":
            print(auto.disable())
        else:
            print("開機自啟：" + ("已啟用" if auto.is_enabled() else "未啟用"))
            print(f"路徑：{auto.startup_path()}")
        raise SystemExit(0)

    if raw and raw[0] == "listen":
        from jarvis.ear import listen_once

        seconds = float(raw[1]) if len(raw) > 1 else 3.0
        print(f"[ear] 錄音 {seconds}s …")
        try:
            text = listen_once(seconds=seconds)
        except RuntimeError as exc:
            print(f"[fail] {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        print(f"[ear] {text!r}")
        if text.strip():
            raise SystemExit(run_utterance(text.strip()))
        print("[fail] 無辨識文字")
        raise SystemExit(1)

    parser = argparse.ArgumentParser(prog="jarvis", description="JARVIS Hands + Shell")
    parser.add_argument("utterance", nargs="*", help="例如：open CS2 / 開 MC")
    parser.add_argument("--dry-run", action="store_true", help="只解析，不啟動")
    parser.add_argument("-c", "--command", help="整句指令")
    args = parser.parse_args(raw)

    if args.command:
        text = args.command
    elif args.utterance:
        text = " ".join(args.utterance)
    else:
        parser.print_help()
        print("\n啟動介面：python -m jarvis serve")
        print("開機自啟：python -m jarvis autostart on|off|status")
        print("語音一次：python -m jarvis listen [秒]")
        raise SystemExit(2)

    try:
        code = run_utterance(text, dry_run=args.dry_run)
    except Exception as exc:  # noqa: BLE001
        print(f"[fail] {exc}", file=sys.stderr)
        code = 2
    raise SystemExit(code)


if __name__ == "__main__":
    main()

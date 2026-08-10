"""CLI entry: python -m jarvis -c \"open CS2\" | serve | autostart"""

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
            if auto.has_legacy_cmd():
                print("[warn] 仍有舊 JARVIS.cmd（會彈黑窗）→ 跑：python -m jarvis autostart on")
        raise SystemExit(0)

    if raw and raw[0] == "cursor-hooks":
        from jarvis import cursor_hooks as ch

        sub = raw[1] if len(raw) > 1 else "status"
        if sub in ("on", "install"):
            print(ch.install())
        elif sub in ("off", "uninstall"):
            print(ch.uninstall())
        else:
            print(ch.status())
        raise SystemExit(0)

    if raw and raw[0] == "listen":
        print(
            "[fail] 語音識別已移除。請用：python -m jarvis -c \"開 Cursor\"",
            file=sys.stderr,
        )
        raise SystemExit(2)

    if raw and raw[0] == "wake":
        print(
            "[fail] 聽候已移除。請用：python -m jarvis serve（打字）",
            file=sys.stderr,
        )
        raise SystemExit(2)

    if raw and raw[0] == "aliases":
        from jarvis import memory as mem

        sub = raw[1] if len(raw) > 1 else "list"
        if sub == "clear":
            mem.clear_stt_aliases()
            print("[ok] 已清空 learned stt_aliases")
            raise SystemExit(0)
        learned = mem.list_stt_aliases()
        if not learned:
            print("(無 learned aliases)")
        else:
            for k, v in learned.items():
                print(f"{k} → {v}")
        try:
            from jarvis.config import load_registry

            static = load_registry().stt_aliases
            if static:
                print("--- profiles.yaml stt_aliases ---")
                for k, v in static.items():
                    print(f"{k} → {v}")
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] 讀 profiles 失敗：{exc}", file=sys.stderr)
        raise SystemExit(0)

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
        print("Cursor hook：python -m jarvis cursor-hooks install|status|off")
        print("別名：python -m jarvis aliases | aliases clear")
        raise SystemExit(2)

    try:
        code = run_utterance(text, dry_run=args.dry_run)
    except Exception as exc:  # noqa: BLE001
        print(f"[fail] {exc}", file=sys.stderr)
        code = 2
    raise SystemExit(code)


if __name__ == "__main__":
    main()

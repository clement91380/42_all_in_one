"""CLI interface for norminette-auto-formatter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..core import NorminetteFormatter


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="naf",
        description="Norminette Auto-Formatter — diagnose and fix 42 norm errors",
    )
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Check files for norm errors")
    check_parser.add_argument("files", nargs="+", help="Files to check")
    check_parser.add_argument("--json", action="store_true", help="Output as JSON")

    fix_parser = subparsers.add_parser("fix", help="Auto-fix norm errors")
    fix_parser.add_argument("files", nargs="+", help="Files to fix")
    fix_parser.add_argument("--dry-run", action="store_true", help="Show fixes without applying")
    fix_parser.add_argument("--passes", type=int, default=5, help="Max fix passes (default: 5)")

    subparsers.add_parser("server", help="Start the LSP server")

    return parser


def cmd_check(args: argparse.Namespace) -> int:
    formatter = NorminetteFormatter()
    has_errors = False

    for file_path in args.files:
        path = Path(file_path)
        if not path.exists():
            print(f"Error: {file_path} not found", file=sys.stderr)
            continue

        diagnostics = formatter.diagnose_file(str(path))
        if not diagnostics:
            print(f"✓ {path.name}: OK")
            continue

        has_errors = True
        if args.json:
            import json
            print(json.dumps([d.to_dict() for d in diagnostics], indent=2))
        else:
            print(f"✗ {path.name}: {len(diagnostics)} error(s)")
            for d in diagnostics:
                print(f"  L{d.line}:{d.col} [{d.code}] {d.message}")

    return 1 if has_errors else 0


def cmd_fix(args: argparse.Namespace) -> int:
    formatter = NorminetteFormatter()

    for file_path in args.files:
        path = Path(file_path)
        if not path.exists():
            print(f"Error: {file_path} not found", file=sys.stderr)
            continue

        if args.dry_run:
            source = path.read_text()
            diagnostics = formatter.diagnose_file(str(path))
            from ..core.fixer import compute_fixes
            fixes = compute_fixes(source, diagnostics)
            print(f"{path.name}: {len(fixes)} fix(es) available")
            for fix in fixes:
                print(f"  L{fix.line}: {fix.description}")
        else:
            result = formatter.format_file(str(path), max_passes=args.passes)
            applied = len(result.applied)
            skipped = len(result.skipped)
            print(f"{path.name}: {applied} fix(es) applied, {skipped} skipped")

    return 0


def cmd_server() -> int:
    from ..server.lsp import start_server
    start_server()
    return 0


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "check":
        return cmd_check(args)
    elif args.command == "fix":
        return cmd_fix(args)
    elif args.command == "server":
        return cmd_server()

    return 0


if __name__ == "__main__":
    sys.exit(main())

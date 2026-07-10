"""Main entry point for 42 All-in-One.

Usage:
  42aio                    Launch GUI
  42aio .                  Check current directory (norm + compile)
  42aio check *.c          Check specific files
  42aio check . --depth 2  Check directory, depth limit
  42aio fix .              Auto-fix whole project
  42aio repo URL           Check a GitHub repo
  42aio exam               Browse exam exercises
  42aio predict .          Predict project grade
  42aio server             Start LSP server
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="42aio",
        description="42 All-in-One — accelerate your 42 learning",
    )
    parser.add_argument("--gui", action="store_true", help="Force GUI mode")

    subparsers = parser.add_subparsers(dest="command")

    # check: accepts files OR directories OR "." with optional flags
    check = subparsers.add_parser("check", help="Check files/folders (norm + compile)")
    check.add_argument("paths", nargs="*", default=["."],
                       help="Files or directories (default: current directory)")
    check.add_argument("--depth", type=int, default=None, help="Max scan depth")
    check.add_argument("--pattern", type=str, default=None,
                       help="Glob pattern: ft_*.c")
    check.add_argument("--no-norm",    action="store_true", help="Skip norminette")
    check.add_argument("--no-compile", action="store_true", help="Skip compilation")
    check.add_argument("--json",       action="store_true", help="JSON output")
    check.add_argument("--summary",    action="store_true", help="Summary only")

    # fix
    fix = subparsers.add_parser("fix", help="Auto-fix norm errors")
    fix.add_argument("paths", nargs="*", default=["."])
    fix.add_argument("--depth",   type=int,  default=None)
    fix.add_argument("--pattern", type=str,  default=None)
    fix.add_argument("--dry-run", action="store_true")

    # repo
    repo = subparsers.add_parser("repo", help="Check a GitHub repo")
    repo.add_argument("url")

    # exam
    exam = subparsers.add_parser("exam", help="Browse exam exercises")
    exam.add_argument("--rank",   type=int, choices=[2, 3, 4, 5, 6])
    exam.add_argument("--search", type=str)

    # predict
    predict = subparsers.add_parser("predict", help="Predict project grade")
    predict.add_argument("path", nargs="?", default=".")
    predict.add_argument("--project", type=str, default="auto")

    subparsers.add_parser("server", help="Start LSP server")

    return parser


# ---------------------------------------------------------------
# Resolve paths to a flat list of files
# ---------------------------------------------------------------

def _resolve_paths(paths: list[str], depth=None, pattern=None) -> list[Path]:
    from forty_two_aio.core.file_scanner import scan_directory

    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            patterns = [pattern] if pattern else None
            result = scan_directory(path, depth=depth, patterns=patterns)
            files.extend(f.path for f in result.files)
        elif path.is_file():
            files.append(path)
        else:
            # Glob expansion already done by shell, but try anyway
            import glob
            matched = glob.glob(p, recursive=True)
            for m in matched:
                mp = Path(m)
                if mp.is_file() and mp.suffix in (".c", ".h"):
                    files.append(mp)
    return files


# ---------------------------------------------------------------
# Commands
# ---------------------------------------------------------------

def cmd_check(args):
    import json as _json
    from norminette_formatter.core import NorminetteFormatter
    from forty_two_aio.modules.compiler.checker import (
        check_compilation, check_main_commented_or_missing
    )

    formatter = NorminetteFormatter()
    files = _resolve_paths(args.paths, args.depth, args.pattern)

    if not files:
        print("No .c/.h files found.")
        return 1

    results = []
    total_norm = 0
    total_fail = 0

    for path in files:
        entry = {"file": str(path), "norm": [], "compile": None, "main": None}

        if not args.no_norm and path.suffix in (".c", ".h"):
            try:
                diags = formatter.diagnose_file(str(path))
                total_norm += len(diags)
                entry["norm"] = [d.to_dict() for d in diags]
            except RuntimeError as e:
                entry["norm_error"] = str(e)

        if not args.no_compile and path.suffix == ".c":
            source = path.read_text(errors="replace")
            main_check = check_main_commented_or_missing(source)
            entry["main"] = main_check

            comp = check_compilation(str(path))
            entry["compile"] = {"ok": comp.success, "errors": comp.errors}
            if not comp.success:
                total_fail += 1

        results.append(entry)

    if args.json:
        print(_json.dumps(results, indent=2))
        return 0

    if args.summary:
        norm_files = sum(1 for r in results if r["norm"])
        fail_files = sum(1 for r in results if r.get("compile") and not r["compile"]["ok"])
        print(f"Files checked : {len(files)}")
        print(f"Norm errors   : {total_norm} in {norm_files} file(s)")
        print(f"Compile fails : {fail_files} file(s)")
        return 0

    for entry in results:
        path = entry["file"]
        norm = entry["norm"]
        comp = entry.get("compile")
        main = entry.get("main")

        has_issue = norm or (comp and not comp["ok"]) or (main and main.get("main_commented"))
        if not has_issue:
            if not args.summary:
                print(f"  OK  {path}")
            continue

        print(f"\n--- {path} ---")
        if norm:
            print(f"  Norm: {len(norm)} error(s)")
            for d in norm[:5]:
                print(f"    L{d['line']}:{d['col']} [{d['code']}] {d['message']}")
            if len(norm) > 5:
                print(f"    ... {len(norm)-5} more")

        if main and main.get("main_commented"):
            print(f"  WARNING: main() is COMMENTED OUT (line {main['main_line']})")

        if comp and not comp["ok"]:
            print(f"  Compile: FAIL")
            for e in comp["errors"][:3]:
                print(f"    {e}")

    print(f"\n{'='*40}")
    print(f"  {len(files)} files | {total_norm} norm errors | {total_fail} compile fail(s)")
    return 1 if (total_norm or total_fail) else 0


def cmd_fix(args):
    from norminette_formatter.core import NorminetteFormatter

    formatter = NorminetteFormatter()
    files = _resolve_paths(args.paths, args.depth, args.pattern)

    if not files:
        print("No .c/.h files found.")
        return 1

    total_fixed = 0
    for path in files:
        try:
            if args.dry_run:
                from forty_two_aio.core.file_scanner import scan_directory
                source = path.read_text(errors="replace")
                diags = formatter.diagnose_source(source, str(path))
                from norminette_formatter.core.fixer import compute_fixes
                fixes = compute_fixes(source, diags)
                if fixes:
                    print(f"  {path.name}: {len(fixes)} fix(es) available")
                    for fx in fixes[:3]:
                        print(f"    L{fx.line}: {fx.description}")
            else:
                result = formatter.format_file(str(path))
                applied = len(result.applied)
                total_fixed += applied
                if applied:
                    print(f"  {path.name}: {applied} fixed")
        except RuntimeError as e:
            print(f"  ERROR {path.name}: {e}")

    if not args.dry_run:
        print(f"\n{total_fixed} total fix(es) applied in {len(files)} file(s)")
    return 0


def cmd_repo(args):
    from forty_two_aio.modules.github.repo_checker import check_repo

    print(f"Cloning and checking {args.url}...")
    result = check_repo(args.url)
    print(f"Files: {len(result.c_files)} .c  {len(result.h_files)} .h")
    print(f"Makefile: {'yes' if result.makefile_found else 'no'}")
    if result.main_issues:
        print("\nmain() issues:")
        for i in result.main_issues:
            print(f"  {i['file']}: {i['issue']} (L{i['line']})")
    print(f"\nCompilation:")
    for c in result.compilation_results:
        print(f"  {'OK  ' if c['success'] else 'FAIL'} {c['file']}")
    if result.issues:
        print(f"\nIssues:")
        for i in result.issues:
            print(f"  - {i}")
    print(f"\nScore: {result.score}/100")
    return 0


def cmd_exam(args):
    from forty_two_aio.modules.exams.database import (
        get_exercises_by_rank, search_exercises, EXAM_DATABASE
    )

    if args.search:
        exercises = search_exercises(args.search)
    elif args.rank:
        exercises = get_exercises_by_rank(args.rank)
    else:
        exercises = EXAM_DATABASE

    print(f"\n{len(exercises)} exercise(s):\n")
    for ex in exercises:
        print(f"  [R{ex.rank}] {ex.name:<25} {'*'*ex.difficulty:<5} ({', '.join(ex.topics)})")

    if len(exercises) == 1:
        ex = exercises[0]
        print(f"\n{'='*50}\n  {ex.name}\n{'='*50}\n\n{ex.subject}")
        if ex.hints:
            print("\nHints:")
            for h in ex.hints:
                print(f"  - {h}")
    return 0


def cmd_predict(args):
    from forty_two_aio.core.file_scanner import scan_directory
    from forty_two_aio.modules.compiler.checker import check_compilation
    from forty_two_aio.modules.predictor.grade_predictor import (
        detect_project_from_files, predict_grade
    )

    folder = Path(args.path)
    if not folder.is_dir():
        print(f"Not a directory: {args.path}")
        return 1

    result = scan_directory(folder)
    all_names = [f.name for f in result.files]
    project = args.project if args.project != "auto" else detect_project_from_files(all_names)
    print(f"Project detected: {project}")

    checks = {}
    compile_ok = all(
        check_compilation(str(f.path)).success for f in result.c_files
    )
    checks["compilation"] = compile_ok
    print(f"Compilation: {'PASS' if compile_ok else 'FAIL'}")

    prediction = predict_grade(project, checks)
    print(f"\nEstimated score : {prediction.estimated_score}/125")
    print(f"Would pass      : {'YES' if prediction.would_pass else 'NO'}")
    print(f"Confidence      : {prediction.confidence}")
    for c in prediction.criteria:
        print(f"  {'PASS' if c.passed else 'FAIL'} {c.name} ({c.weight:.0%})")
    return 0


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------

def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    # "42aio ." or "42aio" with no subcommand and a path-like arg — check that path
    if args.command is None and not args.gui:
        # Check if first positional looks like a path (handles: 42aio . 42aio src/)
        argv_rest = [a for a in sys.argv[1:] if not a.startswith("-")]
        if argv_rest and Path(argv_rest[0]).exists():
            # Treat as: 42aio check <path>
            sys.argv = [sys.argv[0], "check"] + argv_rest
            args = parser.parse_args()
        else:
            from forty_two_aio.gui.app import run
            run()
            return 0

    if args.gui:
        from forty_two_aio.gui.app import run
        run()
        return 0

    dispatch = {
        "check":   cmd_check,
        "fix":     cmd_fix,
        "repo":    cmd_repo,
        "exam":    cmd_exam,
        "predict": cmd_predict,
        "server":  lambda _: __import__(
            "norminette_formatter.server.lsp", fromlist=["start_server"]
        ).start_server(),
    }

    fn = dispatch.get(args.command)
    if fn:
        return fn(args) or 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

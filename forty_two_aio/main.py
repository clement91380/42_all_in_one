"""Main entry point for 42 All-in-One."""

from __future__ import annotations

import argparse
import sys


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="42aio",
        description="42 All-in-One — accelerate your 42 learning",
    )
    parser.add_argument("--gui", action="store_true", help="Launch GUI mode")

    subparsers = parser.add_subparsers(dest="command")

    check = subparsers.add_parser("check", help="Check files (norm + compile)")
    check.add_argument("files", nargs="+")
    check.add_argument("--no-norm", action="store_true")
    check.add_argument("--no-compile", action="store_true")

    fix = subparsers.add_parser("fix", help="Auto-fix norm errors")
    fix.add_argument("files", nargs="+")

    repo = subparsers.add_parser("repo", help="Check a GitHub repo")
    repo.add_argument("url", help="Repository URL")

    exam = subparsers.add_parser("exam", help="Browse exam exercises")
    exam.add_argument("--rank", type=int, choices=[2, 3, 4, 5, 6])
    exam.add_argument("--search", type=str)

    predict = subparsers.add_parser("predict", help="Predict project grade")
    predict.add_argument("path", help="Project folder path")
    predict.add_argument("--project", type=str, default="auto")

    subparsers.add_parser("server", help="Start LSP server")

    return parser


def cmd_check(args):
    from pathlib import Path
    from norminette_formatter.core import NorminetteFormatter
    from forty_two_aio.modules.compiler.checker import check_compilation, check_main_commented_or_missing

    formatter = NorminetteFormatter()

    for f in args.files:
        path = Path(f)
        if not path.exists():
            print(f"[ERROR] {f}: not found")
            continue

        print(f"\n--- {path.name} ---")

        if not args.no_norm:
            try:
                diags = formatter.diagnose_file(str(path))
                if diags:
                    print(f"  NORM: {len(diags)} error(s)")
                    for d in diags:
                        print(f"    L{d.line}:{d.col} [{d.code}] {d.message}")
                else:
                    print("  NORM: OK")
            except RuntimeError as e:
                print(f"  NORM: {e}")

        if not args.no_compile and f.endswith(".c"):
            source = path.read_text(errors="replace")
            main_check = check_main_commented_or_missing(source)
            if main_check["main_commented"]:
                print(f"  MAIN: COMMENTED OUT (line {main_check['main_line']})")
            elif not main_check["has_main"]:
                print("  MAIN: not found (library file)")

            result = check_compilation(str(path))
            if result.success:
                print("  COMPILE: OK")
            else:
                print("  COMPILE: FAIL")
                for err in result.errors[:5]:
                    print(f"    {err}")


def cmd_fix(args):
    from pathlib import Path
    from norminette_formatter.core import NorminetteFormatter

    formatter = NorminetteFormatter()
    for f in args.files:
        path = Path(f)
        if not path.exists():
            print(f"[ERROR] {f}: not found")
            continue
        result = formatter.format_file(str(path))
        print(f"{path.name}: {len(result.applied)} fixed, {len(result.skipped)} skipped")


def cmd_repo(args):
    from forty_two_aio.modules.github.repo_checker import check_repo

    print(f"Checking {args.url}...")
    result = check_repo(args.url)
    print(f"\nFiles: {len(result.c_files)} .c, {len(result.h_files)} .h")
    print(f"Makefile: {'Yes' if result.makefile_found else 'No'}")

    if result.main_issues:
        print("\nMAIN ISSUES:")
        for issue in result.main_issues:
            print(f"  {issue['file']}: {issue['issue']}")

    print(f"\nCompilation:")
    for comp in result.compilation_results:
        status = "OK" if comp["success"] else "FAIL"
        print(f"  [{status}] {comp['file']}")

    print(f"\nScore: {result.score}/100")

    if result.issues:
        print("\nIssues:")
        for issue in result.issues:
            print(f"  - {issue}")


def cmd_exam(args):
    from forty_two_aio.modules.exams.database import get_exercises_by_rank, search_exercises, EXAM_DATABASE

    if args.search:
        exercises = search_exercises(args.search)
    elif args.rank:
        exercises = get_exercises_by_rank(args.rank)
    else:
        exercises = EXAM_DATABASE

    print(f"\n{len(exercises)} exercise(s):\n")
    for ex in exercises:
        diff = "*" * ex.difficulty
        print(f"  [Rank {ex.rank}] {ex.name:<25} {diff:<5} ({', '.join(ex.topics)})")

    if len(exercises) == 1:
        ex = exercises[0]
        print(f"\n{'='*50}")
        print(f"  {ex.name}")
        print(f"{'='*50}")
        print(f"\n{ex.subject}")
        if ex.hints:
            print("\nHints:")
            for h in ex.hints:
                print(f"  - {h}")


def cmd_predict(args):
    from pathlib import Path
    from forty_two_aio.modules.compiler.checker import check_compilation
    from forty_two_aio.modules.predictor.grade_predictor import detect_project_from_files, predict_grade

    folder = Path(args.path)
    if not folder.is_dir():
        print(f"Error: {args.path} is not a directory")
        return

    c_files = list(folder.rglob("*.c"))
    h_files = list(folder.rglob("*.h"))
    all_files = [str(f.relative_to(folder)) for f in c_files + h_files]

    project = args.project if args.project != "auto" else detect_project_from_files(all_files)
    print(f"Project: {project}")

    checks = {}
    compile_ok = all(check_compilation(str(f)).success for f in c_files)
    checks["compilation"] = compile_ok
    print(f"Compilation: {'PASS' if compile_ok else 'FAIL'}")

    prediction = predict_grade(project, checks)
    print(f"\nEstimated score: {prediction.estimated_score}/125")
    print(f"Would pass: {'YES' if prediction.would_pass else 'NO'}")
    print(f"Confidence: {prediction.confidence}")


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    if args.gui or args.command is None:
        from forty_two_aio.gui.app import run
        run()
        return 0

    if args.command == "check":
        cmd_check(args)
    elif args.command == "fix":
        cmd_fix(args)
    elif args.command == "repo":
        cmd_repo(args)
    elif args.command == "exam":
        cmd_exam(args)
    elif args.command == "predict":
        cmd_predict(args)
    elif args.command == "server":
        from norminette_formatter.server.lsp import start_server
        start_server()

    return 0


if __name__ == "__main__":
    sys.exit(main())

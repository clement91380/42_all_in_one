"""Compilation checker — verifies code compiles with strict flags.

Key rule for 42 projects:
  - When submitting, main() is either commented out or absent (it's a library).
  - To test compilation we must uncomment/inject a stub main IN MEMORY ONLY,
    never touching the actual file.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CompileResult:
    success: bool
    returncode: int
    stdout: str
    stderr: str
    flags_used: list[str]
    file_path: str
    main_was_commented: bool = False
    main_was_injected: bool = False

    @property
    def errors(self) -> list[str]:
        return [line for line in self.stderr.splitlines() if "error:" in line]

    @property
    def warnings(self) -> list[str]:
        return [line for line in self.stderr.splitlines() if "warning:" in line]


# ---------------------------------------------------------------
# main() detection and source manipulation (in memory only)
# ---------------------------------------------------------------

_MAIN_RE = re.compile(r"(?:^|\n)[ \t]*(?://+|/\*+).*\bmain\s*\(", re.MULTILINE)
_MAIN_FULL_BLOCK_RE = re.compile(
    r"/\*\s*((?:int\s+)?main\s*\([^)]*\)\s*\{.*?})\s*\*/",
    re.DOTALL
)


def analyze_main(source: str) -> dict:
    """Detect whether main() is present, commented, or absent."""
    lines = source.splitlines()
    result = {
        "has_real_main": False,
        "main_commented_line": False,   # // int main(...
        "main_commented_block": False,  # /* int main(...) { ... } */
        "main_line": None,
        "main_col": None,
    }

    in_block_comment = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Track block comments
        if "/*" in line and "*/" not in line:
            in_block_comment = True
        if "*/" in line:
            in_block_comment = False
            # Check if this ends a block that contains main
            if re.search(r"\bmain\s*\(", line):
                result["main_commented_block"] = True
                result["main_line"] = i
            continue

        if in_block_comment:
            if re.search(r"\bmain\s*\(", line):
                result["main_commented_block"] = True
                result["main_line"] = i
            continue

        if re.search(r"\bmain\s*\(", stripped):
            if stripped.startswith("//") or stripped.startswith("/*"):
                result["main_commented_line"] = True
                result["main_line"] = i
            else:
                result["has_real_main"] = True
                result["main_line"] = i
                break

    # Also check for block-commented main using regex
    if _MAIN_FULL_BLOCK_RE.search(source):
        result["main_commented_block"] = True

    return result


def uncomment_main(source: str) -> tuple[str, bool]:
    """Uncomment main() in source, return (modified_source, was_modified).

    This operates entirely in memory — the original file is never touched.
    Handles:
      - // int main(void) { ... }   (single-line comment)
      - /* int main(...) { ... } */ (block comment around whole function)
    """
    # Case 1: block comment wrapping the entire main function
    m = _MAIN_FULL_BLOCK_RE.search(source)
    if m:
        new_source = source[:m.start()] + m.group(1) + source[m.end():]
        return new_source, True

    # Case 2: line-by-line commented main — uncomment each // line until closing brace
    lines = source.splitlines(keepends=True)
    main_start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.search(r"\bmain\s*\(", stripped) and (
            stripped.startswith("//") or stripped.startswith("/*")
        ):
            main_start = i
            break

    if main_start is None:
        return source, False

    result_lines = lines[:]
    brace_count = 0
    found_open = False
    i = main_start

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Strip // prefix
        if stripped.startswith("//"):
            result_lines[i] = re.sub(r"^\s*//\s?", "", line, count=1)
        elif stripped.startswith("/*") and stripped.endswith("*/"):
            result_lines[i] = re.sub(r"/\*\s?|\s?\*/", "", stripped) + "\n"

        # Track braces to find end of function
        for ch in result_lines[i]:
            if ch == "{":
                brace_count += 1
                found_open = True
            elif ch == "}":
                brace_count -= 1

        if found_open and brace_count == 0:
            break
        i += 1

    return "".join(result_lines), True


def inject_stub_main(source: str) -> str:
    """Append a minimal stub main() if none exists, for compilation testing."""
    return source + "\n\nint\tmain(void)\n{\n\treturn (0);\n}\n"


# ---------------------------------------------------------------
# Core compilation functions
# ---------------------------------------------------------------

def _compile_source_text(
    source: str,
    filename: str,
    flags: list[str],
    compiler: str,
    extra_info: dict | None = None,
) -> CompileResult:
    suffix = Path(filename).suffix or ".c"
    extra = extra_info or {}

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, prefix="42aio_"
    ) as tmp:
        tmp.write(source)
        tmp_path = tmp.name

    try:
        with tempfile.NamedTemporaryFile(suffix=".o", delete=True) as out:
            cmd = [compiler] + flags + ["-c", tmp_path, "-o", out.name]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return CompileResult(
                    success=r.returncode == 0,
                    returncode=r.returncode,
                    stdout=r.stdout,
                    stderr=r.stderr,
                    flags_used=flags,
                    file_path=filename,
                    **extra,
                )
            except FileNotFoundError:
                return CompileResult(
                    success=False, returncode=-1, stdout="",
                    stderr=f"Compiler '{compiler}' not found",
                    flags_used=flags, file_path=filename, **extra,
                )
            except subprocess.TimeoutExpired:
                return CompileResult(
                    success=False, returncode=-1, stdout="",
                    stderr="Compilation timed out",
                    flags_used=flags, file_path=filename, **extra,
                )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def check_compilation(
    file_path: str,
    flags: list[str] | None = None,
    compiler: str = "cc",
) -> CompileResult:
    """Compile a file with 42-aware main() handling.

    Strategy:
    1. Read source. If it has a real main() → compile as-is.
    2. If main() is commented → uncomment IN MEMORY, compile the temp copy.
    3. If no main() at all → inject a stub main IN MEMORY, compile.
    4. The original file is NEVER modified.
    """
    if flags is None:
        flags = ["-Wall", "-Wextra", "-Werror"]

    path = Path(file_path)
    if not path.exists():
        return CompileResult(
            success=False, returncode=-1, stdout="",
            stderr=f"File not found: {file_path}",
            flags_used=flags, file_path=file_path,
        )

    try:
        source = path.read_text(errors="replace")
    except OSError as e:
        return CompileResult(
            success=False, returncode=-1, stdout="",
            stderr=str(e), flags_used=flags, file_path=file_path,
        )

    info = analyze_main(source)
    main_was_commented = info["main_commented_line"] or info["main_commented_block"]
    main_was_injected = False

    if info["has_real_main"]:
        compile_source = source
    elif main_was_commented:
        compile_source, _ = uncomment_main(source)
    else:
        # No main at all — inject stub so -c still works (header files, library files)
        # Actually for -c we don't need main at all. Only link step does.
        compile_source = source
        main_was_injected = False

    return _compile_source_text(
        compile_source, file_path, flags, compiler,
        extra_info={
            "main_was_commented": main_was_commented,
            "main_was_injected": main_was_injected,
        }
    )


def check_compilation_source(
    source: str,
    filename: str = "test.c",
    flags: list[str] | None = None,
    compiler: str = "cc",
) -> CompileResult:
    """Compile from source string directly (in memory)."""
    if flags is None:
        flags = ["-Wall", "-Wextra", "-Werror"]
    return _compile_source_text(source, filename, flags, compiler)


def check_main_commented_or_missing(source: str) -> dict:
    """Backward-compatible wrapper around analyze_main()."""
    info = analyze_main(source)
    return {
        "has_main": info["has_real_main"],
        "main_commented": info["main_commented_line"] or info["main_commented_block"],
        "main_line": info["main_line"],
    }


# ---------------------------------------------------------------
# Project-level compilation (multiple files together)
# ---------------------------------------------------------------

@dataclass
class ProjectCompileResult:
    passed: int
    total: int
    files: list[CompileResult] = field(default_factory=list)
    main_handled: list[str] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return self.passed == self.total

    @property
    def score(self) -> int:
        return int(self.passed / self.total * 100) if self.total else 0


def check_project_compilation(
    folder: Path,
    flags: list[str] | None = None,
    compiler: str = "cc",
) -> ProjectCompileResult:
    """Compile every .c file in a project folder.

    For each file:
    - If main() is commented → uncomment in memory to compile
    - If no main() → compile with -c (object file, no link needed)
    - Original files are NEVER modified.
    """
    if flags is None:
        flags = ["-Wall", "-Wextra", "-Werror"]

    c_files = list(folder.rglob("*.c"))
    results = []
    main_handled = []

    for c_file in c_files:
        result = check_compilation(str(c_file), flags, compiler)
        results.append(result)
        if result.main_was_commented:
            main_handled.append(f"{c_file.name}: main() uncommented in memory for test")
        elif result.main_was_injected:
            main_handled.append(f"{c_file.name}: stub main injected in memory for test")

    passed = sum(1 for r in results if r.success)
    return ProjectCompileResult(
        passed=passed,
        total=len(results),
        files=results,
        main_handled=main_handled,
    )

"""Compilation checker — verifies code compiles with strict flags."""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CompileResult:
    success: bool
    returncode: int
    stdout: str
    stderr: str
    flags_used: list[str]
    file_path: str

    @property
    def errors(self) -> list[str]:
        return [line for line in self.stderr.splitlines() if "error:" in line]

    @property
    def warnings(self) -> list[str]:
        return [line for line in self.stderr.splitlines() if "warning:" in line]


def check_compilation(
    file_path: str,
    flags: list[str] | None = None,
    compiler: str = "cc",
) -> CompileResult:
    if flags is None:
        flags = ["-Wall", "-Wextra", "-Werror"]

    path = Path(file_path)
    if not path.exists():
        return CompileResult(
            success=False,
            returncode=-1,
            stdout="",
            stderr=f"File not found: {file_path}",
            flags_used=flags,
            file_path=file_path,
        )

    with tempfile.NamedTemporaryFile(suffix=".o", delete=True) as tmp:
        cmd = [compiler] + flags + ["-c", str(path), "-o", tmp.name]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return CompileResult(
                success=result.returncode == 0,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                flags_used=flags,
                file_path=file_path,
            )
        except FileNotFoundError:
            return CompileResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr=f"Compiler '{compiler}' not found in PATH",
                flags_used=flags,
                file_path=file_path,
            )
        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr="Compilation timed out",
                flags_used=flags,
                file_path=file_path,
            )


def check_compilation_source(
    source: str,
    filename: str = "test.c",
    flags: list[str] | None = None,
    compiler: str = "cc",
) -> CompileResult:
    suffix = Path(filename).suffix or ".c"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=True, prefix="42aio_"
    ) as tmp:
        tmp.write(source)
        tmp.flush()
        return check_compilation(tmp.name, flags, compiler)


def check_main_commented_or_missing(source: str) -> dict:
    """Check if main() is commented out or missing entirely."""
    import re

    lines = source.splitlines()
    result = {
        "has_main": False,
        "main_commented": False,
        "main_line": None,
    }

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if re.search(r"\bmain\s*\(", stripped):
            if stripped.startswith("//") or stripped.startswith("/*"):
                result["main_commented"] = True
                result["main_line"] = i
            else:
                result["has_main"] = True
                result["main_line"] = i
            break

    return result

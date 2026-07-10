"""Parse norminette output into structured diagnostics."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Diagnostic:
    file: str
    line: int
    col: int
    code: str
    message: str
    severity: Severity = Severity.ERROR

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "col": self.col,
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
        }


_NORM_ERROR_RE = re.compile(
    r"^(?P<type>Error|Notice)\s*:\s*(?P<code>\S+)\s*"
    r"\(line:\s*(?P<line>\d+)(?:,\s*col:\s*(?P<col>\d+))?\)\s*:\s*(?P<msg>.+)$"
)


def run_norminette(file_path: str) -> str:
    try:
        result = subprocess.run(
            ["norminette", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout + result.stderr
    except FileNotFoundError:
        raise RuntimeError("norminette is not installed or not in PATH")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"norminette timed out on {file_path}")


def parse_norminette_output(output: str, file_path: str) -> list[Diagnostic]:
    diagnostics = []
    for line in output.splitlines():
        m = _NORM_ERROR_RE.match(line.strip())
        if not m:
            continue
        severity = Severity.WARNING if m.group("type") == "Notice" else Severity.ERROR
        diagnostics.append(
            Diagnostic(
                file=file_path,
                line=int(m.group("line")),
                col=int(m.group("col")) if m.group("col") else 1,
                code=m.group("code"),
                message=m.group("msg").strip(),
                severity=severity,
            )
        )
    return diagnostics


def run_diagnostics(file_path: str) -> list[Diagnostic]:
    output = run_norminette(file_path)
    return parse_norminette_output(output, file_path)


def run_diagnostics_from_source(source: str, file_path: str) -> list[Diagnostic]:
    """Run norminette on source text via a temp file."""
    import tempfile

    suffix = Path(file_path).suffix or ".c"
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=True) as tmp:
        tmp.write(source)
        tmp.flush()
        output = run_norminette(tmp.name)
        return parse_norminette_output(output, file_path)

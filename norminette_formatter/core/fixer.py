"""Apply fixes to source files based on diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from .diagnostics import Diagnostic
from .rules import Fix, get_fix_for


@dataclass
class FixResult:
    original: str
    fixed: str
    applied: list[Fix]
    skipped: list[Diagnostic]


def compute_fixes(source: str, diagnostics: list[Diagnostic]) -> list[Fix]:
    lines = source.splitlines(keepends=True)
    fixes = []
    for diag in diagnostics:
        fix = get_fix_for(diag.code, lines, diag.line, diag.col)
        if fix is not None:
            fixes.append(fix)
    return fixes


def apply_fixes(source: str, diagnostics: list[Diagnostic]) -> FixResult:
    lines = source.splitlines(keepends=True)
    applied = []
    skipped = []

    sorted_diags = sorted(diagnostics, key=lambda d: d.line, reverse=True)

    for diag in sorted_diags:
        fix = get_fix_for(diag.code, lines, diag.line, diag.col)
        if fix is None:
            skipped.append(diag)
            continue
        idx = fix.line - 1
        if idx < len(lines):
            if fix.new_text == "":
                lines.pop(idx)
            else:
                new_text = fix.new_text if fix.new_text.endswith("\n") else fix.new_text + "\n"
                lines[idx] = new_text
        elif fix.new_text:
            lines.insert(0, fix.new_text)
        applied.append(fix)

    fixed = "".join(lines)
    return FixResult(
        original=source,
        fixed=fixed,
        applied=applied,
        skipped=skipped,
    )

"""Main formatter class — the unified core used by CLI, LSP, and all editors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .diagnostics import Diagnostic, run_diagnostics, run_diagnostics_from_source
from .fixer import FixResult, apply_fixes, compute_fixes
from .rules import Fix


class NorminetteFormatter:
    """Single entry point for all formatting operations.

    Used identically by the CLI, the LSP server, and any editor plugin.
    """

    def diagnose_file(self, file_path: str) -> list[Diagnostic]:
        return run_diagnostics(file_path)

    def diagnose_source(self, source: str, file_path: str) -> list[Diagnostic]:
        return run_diagnostics_from_source(source, file_path)

    def fix_file(self, file_path: str) -> FixResult:
        path = Path(file_path)
        source = path.read_text()
        diagnostics = self.diagnose_file(file_path)
        result = apply_fixes(source, diagnostics)
        if result.fixed != result.original:
            path.write_text(result.fixed)
        return result

    def fix_source(self, source: str, file_path: str) -> FixResult:
        diagnostics = self.diagnose_source(source, file_path)
        return apply_fixes(source, diagnostics)

    def get_fixes(self, source: str, file_path: str) -> list[Fix]:
        diagnostics = self.diagnose_source(source, file_path)
        return compute_fixes(source, diagnostics)

    def format_file(self, file_path: str, max_passes: int = 5) -> FixResult:
        """Run multiple fix passes until no more fixes are applicable."""
        path = Path(file_path)
        source = path.read_text()
        all_applied = []
        all_skipped = []

        for _ in range(max_passes):
            diagnostics = self.diagnose_source(source, file_path)
            if not diagnostics:
                break
            result = apply_fixes(source, diagnostics)
            if result.fixed == source:
                all_skipped.extend(result.skipped)
                break
            all_applied.extend(result.applied)
            all_skipped = list(result.skipped)
            source = result.fixed

        path.write_text(source)
        return FixResult(
            original=path.read_text(),
            fixed=source,
            applied=all_applied,
            skipped=all_skipped,
        )

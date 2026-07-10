"""Tests for the fixer module."""

from norminette_formatter.core.diagnostics import Diagnostic, Severity
from norminette_formatter.core.fixer import apply_fixes


def test_apply_fixes_removes_space_before_func():
    source = "int\tmain (void)\n{\n}\n"
    diags = [
        Diagnostic(file="test.c", line=1, col=1, code="SPACE_BEFORE_FUNC",
                   message="space before func", severity=Severity.ERROR)
    ]
    result = apply_fixes(source, diags)
    assert " (" not in result.fixed
    assert "(" in result.fixed
    assert len(result.applied) == 1


def test_apply_fixes_no_diags():
    source = "int\tmain(void)\n{\n}\n"
    result = apply_fixes(source, [])
    assert result.fixed == source
    assert len(result.applied) == 0


def test_apply_fixes_unknown_code_skipped():
    source = "int\tmain(void)\n{\n}\n"
    diags = [
        Diagnostic(file="test.c", line=1, col=1, code="UNKNOWN_CODE",
                   message="unknown", severity=Severity.ERROR)
    ]
    result = apply_fixes(source, diags)
    assert result.fixed == source
    assert len(result.skipped) == 1

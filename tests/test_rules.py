"""Tests for fix rules."""

from norminette_formatter.core.rules import get_fix_for


def test_fix_space_before_func():
    lines = ["int\tmain (void)\n"]
    fix = get_fix_for("SPACE_BEFORE_FUNC", lines, 1, 1)
    assert fix is not None
    assert "(" in fix.new_text
    assert " (" not in fix.new_text


def test_fix_space_after_keyword():
    lines = ["	if(x == 1)\n"]
    fix = get_fix_for("SPACE_AFTER_KW", lines, 1, 1)
    assert fix is not None
    assert "if (" in fix.new_text


def test_fix_tab_instead_of_space():
    lines = ["    int x;\n"]
    fix = get_fix_for("TAB_INSTEAD_OF_SPACE", lines, 1, 1)
    assert fix is not None
    assert fix.new_text.startswith("\t")


def test_fix_space_empty_line():
    lines = ["   \n"]
    fix = get_fix_for("SPACE_EMPTY_LINE", lines, 1, 1)
    assert fix is not None
    assert fix.new_text == "\n"


def test_fix_wrong_scope_comment():
    lines = ["	// this is a comment\n"]
    fix = get_fix_for("WRONG_SCOPE_COMMENT", lines, 1, 1)
    assert fix is not None
    assert "/*" in fix.new_text
    assert "*/" in fix.new_text
    assert "//" not in fix.new_text


def test_unknown_rule_returns_none():
    lines = ["int main(void)\n"]
    fix = get_fix_for("NONEXISTENT_RULE", lines, 1, 1)
    assert fix is None


def test_fix_space_after_par():
    lines = ["	if( x == 1)\n"]
    fix = get_fix_for("SPC_AFTER_PAR", lines, 1, 1)
    assert fix is not None
    assert "( " not in fix.new_text


def test_fix_space_before_par():
    lines = ["	if (x == 1 )\n"]
    fix = get_fix_for("SPC_BEFORE_PAR", lines, 1, 1)
    assert fix is not None
    assert " )" not in fix.new_text

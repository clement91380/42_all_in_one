"""Fix rules for norminette errors.

Each rule maps a norminette error code to a function that produces
a fix for a given line of source code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


@dataclass
class Fix:
    line: int
    old_text: str
    new_text: str
    description: str


FixFunc = Callable[[list[str], int, int], Fix | None]

_RULES: dict[str, FixFunc] = {}


def rule(code: str):
    def decorator(fn: FixFunc):
        _RULES[code] = fn
        return fn
    return decorator


def get_fix_for(code: str, lines: list[str], line: int, col: int) -> Fix | None:
    fn = _RULES.get(code)
    if fn is None:
        return None
    try:
        return fn(lines, line, col)
    except (IndexError, ValueError):
        return None


# --- Rules ---


@rule("SPACE_BEFORE_FUNC")
def fix_space_before_func(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    new = re.sub(r"\s+\(", "(", old, count=1)
    if new == old:
        return None
    return Fix(line=line, old_text=old, new_text=new, description="Remove space before function parenthesis")


@rule("SPACE_AFTER_KW")
def fix_space_after_kw(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    keywords = ["if", "else", "while", "for", "return", "switch", "case"]
    new = old
    for kw in keywords:
        pattern = rf"\b({kw})\("
        new = re.sub(pattern, rf"\1 (", new)
    if new == old:
        return None
    return Fix(line=line, old_text=old, new_text=new, description=f"Add space after keyword")


@rule("TAB_INSTEAD_OF_SPACE")
@rule("SPACE_REPLACE_TAB")
def fix_tab_instead_of_space(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    leading_spaces = len(old) - len(old.lstrip(" "))
    if leading_spaces == 0:
        return None
    tabs = "\t" * (leading_spaces // 4 + (1 if leading_spaces % 4 else 0))
    new = tabs + old.lstrip(" ")
    if new == old:
        return None
    return Fix(line=line, old_text=old, new_text=new, description="Replace spaces with tabs for indentation")


@rule("SPC_AFTER_OPERATOR")
@rule("SPACE_AFTER_OPERATOR")
def fix_space_after_operator(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    operators = ["+", "-", "*", "/", "=", "==", "!=", "<=", ">=", "<", ">", "&&", "||"]
    new = old
    for op in sorted(operators, key=len, reverse=True):
        escaped = re.escape(op)
        pattern = rf"({escaped})(\S)"
        new = re.sub(pattern, rf"\1 \2", new)
    if new == old:
        return None
    return Fix(line=line, old_text=old, new_text=new, description="Add space after operator")


@rule("SPC_BEFORE_OPERATOR")
@rule("SPACE_BEFORE_OPERATOR")
def fix_space_before_operator(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    operators = ["+", "-", "*", "/", "=", "==", "!=", "<=", ">=", "<", ">", "&&", "||"]
    new = old
    for op in sorted(operators, key=len, reverse=True):
        escaped = re.escape(op)
        pattern = rf"(\S)({escaped})"
        new = re.sub(pattern, rf"\1 \2", new)
    if new == old:
        return None
    return Fix(line=line, old_text=old, new_text=new, description="Add space before operator")


@rule("NO_SPC_AFR_PAR")
@rule("SPC_AFTER_PAR")
def fix_space_after_par(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    new = re.sub(r"\(\s+", "(", old)
    if new == old:
        return None
    return Fix(line=line, old_text=old, new_text=new, description="Remove space after opening parenthesis")


@rule("NO_SPC_BFR_PAR")
@rule("SPC_BEFORE_PAR")
def fix_space_before_par(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    new = re.sub(r"\s+\)", ")", old)
    if new == old:
        return None
    return Fix(line=line, old_text=old, new_text=new, description="Remove space before closing parenthesis")


@rule("NEWLINE_IN_FUNC")
@rule("TOO_MANY_LINES")
def fix_consecutive_newlines(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    if idx > 0 and lines[idx].strip() == "" and lines[idx - 1].strip() == "":
        return Fix(line=line, old_text=lines[idx], new_text="", description="Remove extra blank line")
    return None


@rule("BRACE_NEWLINE")
def fix_brace_newline(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    if old.rstrip().endswith("{") and not old.strip() == "{":
        new = old.rstrip().rstrip("{").rstrip() + "\n" + re.match(r"(\s*)", old).group(1) + "{\n"
        return Fix(line=line, old_text=old, new_text=new, description="Move opening brace to new line")
    return None


@rule("SPACE_EMPTY_LINE")
def fix_space_empty_line(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    if old.strip() == "":
        return Fix(line=line, old_text=old, new_text="\n", description="Remove whitespace from empty line")
    return None


@rule("NL_AFTER_VAR_DECL")
def fix_nl_after_var_decl(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    return Fix(line=line, old_text=old, new_text=old.rstrip() + "\n\n", description="Add newline after variable declarations")


@rule("WRONG_SCOPE_COMMENT")
def fix_wrong_scope_comment(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    if "//" in old:
        new = old[:old.index("//")] + "/* " + old[old.index("//") + 2:].strip() + " */\n"
        return Fix(line=line, old_text=old, new_text=new, description="Convert // comment to /* */ style")
    return None


@rule("LINE_TOO_LONG")
def fix_line_too_long(lines: list[str], line: int, col: int) -> Fix | None:
    idx = line - 1
    old = lines[idx]
    expanded = old.expandtabs(4)
    if len(expanded) <= 80:
        return None
    return Fix(line=line, old_text=old, new_text=old, description="Line exceeds 80 columns (manual fix needed)")


@rule("MISSING_HEADER")
def fix_missing_header(lines: list[str], line: int, col: int) -> Fix | None:
    header = (
        "/* ************************************************************************** */\n"
        "/*                                                                            */\n"
        "/*                                                        :::      ::::::::   */\n"
        "/*   filename.c                                         :+:      :+:    :+:   */\n"
        "/*                                                    +:+ +:+         +:+     */\n"
        "/*   By: user <user@student.42.fr>                  +#+  +:+       +#+        */\n"
        "/*                                                +#+#+#+#+#+   +#+           */\n"
        "/*   Created: 2024/01/01 00:00:00 by user           #+#    #+#             */\n"
        "/*   Updated: 2024/01/01 00:00:00 by user          ###   ########.fr       */\n"
        "/*                                                                            */\n"
        "/* ************************************************************************** */\n"
        "\n"
    )
    return Fix(line=1, old_text="", new_text=header, description="Add 42 header (needs manual edit for user/file info)")


def get_all_rules() -> list[str]:
    return list(_RULES.keys())

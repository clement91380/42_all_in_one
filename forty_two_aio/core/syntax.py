"""C syntax highlighting for tkinter Text widget."""

from __future__ import annotations

import re

# Tag name -> (fg_color_dark, fg_color_light)
TAGS: dict[str, tuple[str, str]] = {
    "keyword":    ("#569cd6", "#0000ff"),
    "type":       ("#4ec9b0", "#267f99"),
    "string":     ("#ce9178", "#a31515"),
    "char":       ("#ce9178", "#a31515"),
    "comment":    ("#6a9955", "#008000"),
    "preproc":    ("#c586c0", "#af00db"),
    "number":     ("#b5cea8", "#098658"),
    "operator":   ("#d4d4d4", "#000000"),
    "function":   ("#dcdcaa", "#795e26"),
    "macro":      ("#9cdcfe", "#001080"),
    "brace":      ("#ffd700", "#8b6914"),
}

C_KEYWORDS = {
    "if", "else", "while", "for", "do", "return", "break", "continue",
    "switch", "case", "default", "goto", "sizeof", "typedef",
    "struct", "union", "enum", "static", "extern", "const", "volatile",
    "register", "auto", "inline", "restrict",
}

C_TYPES = {
    "int", "char", "float", "double", "void", "long", "short",
    "unsigned", "signed", "size_t", "ssize_t", "ptrdiff_t",
    "uint8_t", "uint16_t", "uint32_t", "uint64_t",
    "int8_t", "int16_t", "int32_t", "int64_t",
    "bool", "NULL", "true", "false",
    "t_list", "t_point",
}

_PATTERNS: list[tuple[str, str]] = [
    ("comment",  r"//[^\n]*|/\*[\s\S]*?\*/"),
    ("preproc",  r"^\s*#\s*\w+[^\n]*"),
    ("string",   r'"(?:[^"\\]|\\.)*"'),
    ("char",     r"'(?:[^'\\]|\\.)'"),
    ("number",   r"\b(?:0x[0-9a-fA-F]+|0[0-7]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?[uUlLfF]*)\b"),
    ("keyword",  r"\b(" + "|".join(sorted(C_KEYWORDS, key=len, reverse=True)) + r")\b"),
    ("type",     r"\b(" + "|".join(sorted(C_TYPES,    key=len, reverse=True)) + r")\b"),
    ("function", r"\b([a-zA-Z_]\w*)\s*(?=\()"),
    ("macro",    r"\b[A-Z_][A-Z0-9_]{2,}\b"),
    ("brace",    r"[{}()\[\]]"),
]


def apply_highlighting(text_widget, content: str, theme: str = "dark"):
    """Re-apply syntax highlighting to the entire text widget."""
    col = 1 if theme == "dark" else 0

    # Remove existing tags
    for tag in TAGS:
        text_widget.tag_remove(tag, "1.0", "end")

    for tag, fg in TAGS.items():
        text_widget.tag_configure(tag, foreground=fg[col])

    for tag, pattern in _PATTERNS:
        for m in re.finditer(pattern, content, re.MULTILINE):
            start = _offset_to_index(content, m.start())
            end = _offset_to_index(content, m.end())
            text_widget.tag_add(tag, start, end)

    # comments and strings override everything — raise them
    text_widget.tag_raise("comment")
    text_widget.tag_raise("string")
    text_widget.tag_raise("char")
    text_widget.tag_raise("preproc")


def _offset_to_index(content: str, offset: int) -> str:
    """Convert char offset to 'line.col' tkinter index."""
    before = content[:offset]
    line = before.count("\n") + 1
    col = offset - before.rfind("\n") - 1
    return f"{line}.{col}"


def configure_tags(text_widget, theme: str = "dark"):
    """Configure all tags on a Text widget (call once at init)."""
    col = 1 if theme == "dark" else 0
    for tag, fg in TAGS.items():
        text_widget.tag_configure(tag, foreground=fg[col])

"""Mass file scanner — list C/H files in a directory tree with depth and patterns."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScannedFile:
    path: Path
    rel_path: str
    size: int
    lines: int

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def ext(self) -> str:
        return self.path.suffix


@dataclass
class ScanResult:
    root: Path
    files: list[ScannedFile] = field(default_factory=list)
    total_lines: int = 0
    total_size: int = 0

    @property
    def c_files(self) -> list[ScannedFile]:
        return [f for f in self.files if f.ext == ".c"]

    @property
    def h_files(self) -> list[ScannedFile]:
        return [f for f in self.files if f.ext == ".h"]

    def by_dir(self) -> dict[str, list[ScannedFile]]:
        groups: dict[str, list[ScannedFile]] = {}
        for f in self.files:
            d = str(f.path.parent.relative_to(self.root))
            groups.setdefault(d, []).append(f)
        return groups


def scan_directory(
    root: str | Path,
    extensions: list[str] | None = None,
    depth: int | None = None,
    patterns: list[str] | None = None,
    exclude: list[str] | None = None,
) -> ScanResult:
    """Scan root for C/H files.

    Args:
        root:       Directory to scan.
        extensions: List of extensions to include, e.g. [".c", ".h"]. Default: [".c", ".h"].
        depth:      Max recursion depth. None = unlimited.
        patterns:   Glob patterns to include, e.g. ["ft_*.c", "*list*"].
        exclude:    Directory names to skip, e.g. [".git", "obj"].
    """
    root = Path(root)
    if extensions is None:
        extensions = [".c", ".h"]
    if exclude is None:
        exclude = [".git", ".venv", "__pycache__", "obj", ".o", "a.out"]

    result = ScanResult(root=root)

    def _walk(path: Path, current_depth: int):
        if depth is not None and current_depth > depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return

        for entry in entries:
            if entry.name in exclude or entry.name.startswith("."):
                continue
            if entry.is_dir():
                _walk(entry, current_depth + 1)
            elif entry.is_file() and entry.suffix in extensions:
                if patterns:
                    if not any(fnmatch.fnmatch(entry.name, p) for p in patterns):
                        continue
                try:
                    content = entry.read_text(errors="replace")
                    lines = content.count("\n") + 1
                    size = entry.stat().st_size
                    rel = str(entry.relative_to(root))
                    result.files.append(ScannedFile(
                        path=entry, rel_path=rel, size=size, lines=lines
                    ))
                    result.total_lines += lines
                    result.total_size += size
                except OSError:
                    pass

    _walk(root, 0)
    return result

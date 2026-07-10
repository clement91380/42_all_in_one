"""GitHub repo checker — clone and verify 42 project repos."""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from ..compiler.checker import check_compilation, check_main_commented_or_missing


@dataclass
class RepoCheckResult:
    repo_url: str
    files_found: list[str] = field(default_factory=list)
    c_files: list[str] = field(default_factory=list)
    h_files: list[str] = field(default_factory=list)
    makefile_found: bool = False
    compilation_results: list[dict] = field(default_factory=list)
    main_issues: list[dict] = field(default_factory=list)
    norm_errors: int = 0
    score: int = 0
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def clone_repo(repo_url: str, dest: str) -> bool:
    try:
        subprocess.run(
            ["git", "clone", "--depth=1", repo_url, dest],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_repo(repo_url: str, flags: list[str] | None = None) -> RepoCheckResult:
    if flags is None:
        flags = ["-Wall", "-Wextra", "-Werror"]

    result = RepoCheckResult(repo_url=repo_url)

    with tempfile.TemporaryDirectory(prefix="42aio_") as tmpdir:
        if not clone_repo(repo_url, tmpdir):
            result.issues.append("Failed to clone repository")
            return result

        repo_path = Path(tmpdir)

        all_files = list(repo_path.rglob("*"))
        result.files_found = [str(f.relative_to(repo_path)) for f in all_files if f.is_file()]
        result.c_files = [f for f in result.files_found if f.endswith(".c")]
        result.h_files = [f for f in result.files_found if f.endswith(".h")]
        result.makefile_found = any(
            f.name.lower() in ("makefile", "makefile") for f in all_files
        )

        if not result.c_files:
            result.issues.append("No .c files found in repository")
            return result

        for c_file in result.c_files:
            full_path = repo_path / c_file
            source = full_path.read_text(errors="replace")

            main_check = check_main_commented_or_missing(source)
            if main_check["main_commented"]:
                result.main_issues.append({
                    "file": c_file,
                    "issue": "main() is commented out",
                    "line": main_check["main_line"],
                })
                result.issues.append(f"{c_file}: main() is commented out (line {main_check['main_line']})")

            comp_result = check_compilation(str(full_path), flags)
            result.compilation_results.append({
                "file": c_file,
                "success": comp_result.success,
                "errors": comp_result.errors,
                "warnings": comp_result.warnings,
            })
            if not comp_result.success:
                result.issues.append(
                    f"{c_file}: compilation failed with {flags}"
                )

        passed = sum(1 for r in result.compilation_results if r["success"])
        total = len(result.compilation_results)
        if total > 0:
            result.score = int((passed / total) * 100)

        if result.main_issues:
            result.warnings.append(
                f"{len(result.main_issues)} file(s) have main() commented/missing"
            )

    return result

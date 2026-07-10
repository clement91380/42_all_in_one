"""Git automation — add, commit, push with GitHub CLI integration."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitStatus:
    is_repo: bool
    branch: str
    staged: list[str]
    unstaged: list[str]
    untracked: list[str]
    remote: str
    github_user: str
    ahead: int
    behind: int


@dataclass
class GitResult:
    success: bool
    command: str
    stdout: str
    stderr: str


def _run(cmd: list[str], cwd: str | None = None) -> GitResult:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=30)
        return GitResult(
            success=r.returncode == 0,
            command=" ".join(cmd),
            stdout=r.stdout.strip(),
            stderr=r.stderr.strip(),
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return GitResult(success=False, command=" ".join(cmd), stdout="", stderr=str(e))


def get_github_user() -> str:
    r = _run(["gh", "api", "user", "--jq", ".login"])
    return r.stdout.strip() if r.success else ""


def is_gh_authenticated() -> bool:
    r = _run(["gh", "auth", "status"])
    return r.success


def gh_auth_login() -> GitResult:
    """Returns the raw output of gh auth login so the GUI can display the one-time code."""
    try:
        result = subprocess.run(
            ["gh", "auth", "login", "--web", "-h", "github.com"],
            capture_output=False,     # let output go to terminal / pipe
            text=True,
            timeout=120,
        )
        return GitResult(
            success=result.returncode == 0,
            command="gh auth login",
            stdout="",
            stderr="",
        )
    except FileNotFoundError:
        return GitResult(success=False, command="gh auth login", stdout="",
                         stderr="gh not installed")
    except subprocess.TimeoutExpired:
        return GitResult(success=False, command="gh auth login", stdout="",
                         stderr="Auth timed out")


def get_status(project_path: str) -> GitStatus:
    path = Path(project_path)

    if not (path / ".git").exists():
        return GitStatus(
            is_repo=False, branch="", staged=[], unstaged=[],
            untracked=[], remote="", github_user=get_github_user(),
            ahead=0, behind=0,
        )

    branch_r = _run(["git", "branch", "--show-current"], cwd=project_path)
    branch = branch_r.stdout.strip() if branch_r.success else "unknown"

    remote_r = _run(["git", "remote", "get-url", "origin"], cwd=project_path)
    remote = remote_r.stdout.strip() if remote_r.success else ""

    status_r = _run(["git", "status", "--porcelain"], cwd=project_path)
    staged, unstaged, untracked = [], [], []
    if status_r.success:
        for line in status_r.stdout.splitlines():
            if len(line) < 2:
                continue
            xy = line[:2]
            fname = line[3:].strip()
            if xy[0] != " " and xy[0] != "?":
                staged.append(fname)
            if xy[1] != " " and xy[1] != "?":
                unstaged.append(fname)
            if xy == "??":
                untracked.append(fname)

    ahead, behind = 0, 0
    rev_r = _run(["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"], cwd=project_path)
    if rev_r.success and "\t" in rev_r.stdout:
        parts = rev_r.stdout.split("\t")
        try:
            ahead, behind = int(parts[0]), int(parts[1])
        except ValueError:
            pass

    return GitStatus(
        is_repo=True,
        branch=branch,
        staged=staged,
        unstaged=unstaged,
        untracked=untracked,
        remote=remote,
        github_user=get_github_user(),
        ahead=ahead,
        behind=behind,
    )


def git_init(project_path: str) -> GitResult:
    return _run(["git", "init"], cwd=project_path)


def git_add(project_path: str, files: list[str] | None = None) -> GitResult:
    cmd = ["git", "add"] + (files if files else ["-A"])
    return _run(cmd, cwd=project_path)


def git_commit(project_path: str, message: str, login: str = "") -> GitResult:
    if login:
        full_message = f"{login}: {message}"
    else:
        full_message = message
    return _run(["git", "commit", "-m", full_message], cwd=project_path)


def git_push(project_path: str, branch: str = "") -> GitResult:
    status = get_status(project_path)

    # If no remote set, can't push
    if not status.remote:
        return GitResult(
            success=False,
            command="git push",
            stdout="",
            stderr="No remote configured. Set a remote first.",
        )

    if status.ahead == 0 and not branch:
        # Try push with upstream tracking
        r = _run(["git", "push", "--set-upstream", "origin", status.branch], cwd=project_path)
        if not r.success:
            r = _run(["git", "push"], cwd=project_path)
        return r

    cmd = ["git", "push"]
    if branch:
        cmd += ["origin", branch]
    return _run(cmd, cwd=project_path)


def git_add_commit_push(
    project_path: str,
    message: str,
    login: str = "",
    files: list[str] | None = None,
) -> list[GitResult]:
    results = []

    r_add = git_add(project_path, files)
    results.append(r_add)
    if not r_add.success:
        return results

    r_commit = git_commit(project_path, message, login)
    results.append(r_commit)
    if not r_commit.success:
        return results

    r_push = git_push(project_path)
    results.append(r_push)
    return results


def create_github_repo(name: str, private: bool = False, description: str = "") -> GitResult:
    cmd = ["gh", "repo", "create", name, "--source=.", "--push"]
    if private:
        cmd.append("--private")
    else:
        cmd.append("--public")
    if description:
        cmd += ["--description", description]
    return _run(cmd)


def clone_repo(url: str, dest: str) -> GitResult:
    return _run(["git", "clone", url, dest])

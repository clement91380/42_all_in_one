"""Auto-updater — checks GitHub releases and updates the app."""

from __future__ import annotations

import json
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from ... import __version__

REPO = "clement91380/42_all_in_one"
RELEASES_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
INSTALL_DIR = Path.home() / ".42aio"
SRC_DIR = INSTALL_DIR / "src"


@dataclass
class ReleaseInfo:
    tag: str
    name: str
    body: str
    url: str
    is_newer: bool


def _fetch_latest_release() -> ReleaseInfo | None:
    try:
        req = urllib.request.Request(
            RELEASES_URL,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "42aio"},
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        tag = data.get("tag_name", "").lstrip("v")
        name = data.get("name", tag)
        body = data.get("body", "")
        url = data.get("html_url", "")
        is_newer = _version_gt(tag, __version__)
        return ReleaseInfo(tag=tag, name=name, body=body, url=url, is_newer=is_newer)
    except Exception:
        return None


def _version_gt(a: str, b: str) -> bool:
    def parts(v: str) -> tuple:
        try:
            return tuple(int(x) for x in v.split("."))
        except ValueError:
            return (0,)
    return parts(a) > parts(b)


def check_for_update() -> ReleaseInfo | None:
    release = _fetch_latest_release()
    if release and release.is_newer:
        return release
    return None


def get_latest_release() -> ReleaseInfo | None:
    return _fetch_latest_release()


def do_update() -> tuple[bool, str]:
    """Pull latest code and reinstall. Returns (success, message)."""
    if not SRC_DIR.exists():
        return False, "Installation directory not found. Run the installer again."

    try:
        r = subprocess.run(
            ["git", "pull", "--ff-only"],
            capture_output=True, text=True, cwd=str(SRC_DIR), timeout=30
        )
        if r.returncode != 0:
            return False, f"git pull failed: {r.stderr.strip()}"

        venv_pip = INSTALL_DIR / "venv" / "bin" / "pip"
        if not venv_pip.exists():
            venv_pip = Path("pip")

        r2 = subprocess.run(
            [str(venv_pip), "install", "--quiet", "-e", "."],
            capture_output=True, text=True, cwd=str(SRC_DIR), timeout=60
        )
        if r2.returncode != 0:
            return False, f"pip install failed: {r2.stderr.strip()}"

        return True, r.stdout.strip() or "Already up to date."

    except subprocess.TimeoutExpired:
        return False, "Update timed out."
    except Exception as e:
        return False, str(e)


def get_current_version() -> str:
    return __version__

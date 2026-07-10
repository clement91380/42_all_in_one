"""Global configuration for 42 All-in-One."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

CONFIG_DIR = Path.home() / ".42aio"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Config:
    github_username: str = ""
    github_token: str = ""
    intra_login: str = ""
    default_cc_flags: list[str] = field(default_factory=lambda: ["-Wall", "-Wextra", "-Werror"])
    norminette_enabled: bool = True
    theme: str = "dark"
    language: str = "fr"

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls) -> "Config":
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text())
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()

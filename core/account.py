from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from core.config_loader import PROJECT_ROOT

DEFAULT_ACCOUNTS_PATH = PROJECT_ROOT / "accounts.yaml"


@dataclass
class AccountProfile:
    name: str
    games: dict[str, dict[str, Any]] = field(default_factory=dict)


def load_accounts(path: Path | None = None) -> list[AccountProfile]:
    path = path or DEFAULT_ACCOUNTS_PATH
    if not path.exists():
        return [AccountProfile(name="default")]

    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    accounts = []
    for item in data.get("accounts", []):
        accounts.append(
            AccountProfile(
                name=str(item.get("name", "default")),
                games=dict(item.get("games") or {}),
            )
        )
    return accounts or [AccountProfile(name="default")]

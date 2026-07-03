from __future__ import annotations

from typing import Any, Mapping


def build_step_config(config: Mapping[str, Any], labels: Mapping[str, str]) -> dict[str, bool]:
    return {step_id: bool(config.get(label, True)) for step_id, label in labels.items()}

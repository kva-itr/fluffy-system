"""Загрузка/сохранение пользовательских настроек."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

SETTINGS_FILE = Path.home() / ".max_group_inviter.json"


@dataclass
class Settings:
    id_instance: str = ""
    api_token: str = ""
    api_url: str = ""        # пусто → авто: https://{первые-4-цифры}.api.green-api.com
    group_id: str = ""
    delay: float = 1.5
    appearance: str = "System"
    accent: str = "blue"


def load_settings() -> Settings:
    if SETTINGS_FILE.exists():
        try:
            raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            return Settings(**{k: v for k, v in raw.items() if k in Settings.__dataclass_fields__})
        except Exception:
            pass
    return Settings()


def save_settings(s: Settings) -> None:
    try:
        SETTINGS_FILE.write_text(
            json.dumps(asdict(s), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass

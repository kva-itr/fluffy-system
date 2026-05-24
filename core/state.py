"""Глобальное состояние приложения, разделяемое между видами."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .excel import UserRow
from .settings import Settings


@dataclass
class AppState:
    settings: Settings = field(default_factory=Settings)
    users: List[UserRow] = field(default_factory=list)
    excel_path: Optional[str] = None
    group_info: Optional[dict] = None
    instance_state: Optional[dict] = None

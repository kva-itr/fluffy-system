"""HTTP-клиент GREEN API.

Зелёное API использует per-instance host: `https://{xxxx}.api.green-api.com`,
где `xxxx` — первые 4 цифры `idInstance`. Префикс пути для всех инстансов —
`waInstance` (это нотация самого API, не имеет отношения к выбранному
мессенджеру — MAX, WhatsApp и т.д.).

Эндпоинт строится по шаблону:
    {apiUrl}/waInstance{idInstance}/{method}/{apiTokenInstance}

Если `api_url` не задан (или указан как корневой `https://api.green-api.com`),
он автоматически достраивается до хоста инстанса.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import requests


_DEFAULT_HOST = "https://api.green-api.com"


@dataclass
class GreenApiConfig:
    id_instance: str
    api_token: str
    api_url: str = ""               # пусто → автоопределение по id_instance
    instance_prefix: str = "waInstance"
    timeout: int = 20

    def resolved_api_url(self) -> str:
        """Возвращает реальный хост для запросов.

        Если пользователь оставил поле пустым или указал корневой хост, и
        `idInstance` начинается минимум с 4 цифр — собираем
        `https://{xxxx}.api.green-api.com`.
        """
        url = (self.api_url or "").strip().rstrip("/")
        digits = "".join(ch for ch in self.id_instance if ch.isdigit())
        if (not url or url == _DEFAULT_HOST) and len(digits) >= 4:
            return f"https://{digits[:4]}.api.green-api.com"
        return url or _DEFAULT_HOST


class GreenApiError(Exception):
    pass


class GreenApiClient:
    def __init__(self, config: GreenApiConfig):
        self.config = config

    # ---------- helpers ----------

    def _url(self, method: str) -> str:
        c = self.config
        host = c.resolved_api_url()
        return f"{host}/{c.instance_prefix}{c.id_instance}/{method}/{c.api_token}"

    @staticmethod
    def normalize_phone(raw: str) -> str:
        if raw is None:
            raise GreenApiError("Пустой номер телефона")
        s = str(raw).strip()
        if "@" in s:
            return s
        digits = re.sub(r"\D", "", s)
        if not digits:
            raise GreenApiError(f"Не удалось распознать номер: {raw!r}")
        if len(digits) == 11 and digits.startswith("8"):
            digits = "7" + digits[1:]
        return f"{digits}@c.us"

    @staticmethod
    def normalize_group_id(raw: str) -> str:
        s = str(raw).strip()
        if "@" in s:
            return s
        return f"{s}@g.us"

    # ---------- methods ----------

    def get_state_instance(self) -> dict:
        r = requests.get(self._url("getStateInstance"), timeout=self.config.timeout)
        if not r.ok:
            raise GreenApiError(f"HTTP {r.status_code}: {r.text}")
        return r.json()

    def get_group_data(self, group_id: str) -> dict:
        r = requests.post(
            self._url("getGroupData"),
            json={"groupId": self.normalize_group_id(group_id)},
            timeout=self.config.timeout,
        )
        if not r.ok:
            raise GreenApiError(f"HTTP {r.status_code}: {r.text}")
        return r.json()

    def add_group_participant(self, group_id: str, phone: str) -> dict:
        payload = {
            "groupId": self.normalize_group_id(group_id),
            "participantChatId": self.normalize_phone(phone),
        }
        r = requests.post(self._url("addGroupParticipant"), json=payload, timeout=self.config.timeout)
        try:
            data = r.json()
        except ValueError:
            data = {"raw": r.text}
        if not r.ok:
            raise GreenApiError(f"HTTP {r.status_code}: {data}")
        return data

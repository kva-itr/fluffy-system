"""Клиент для работы с GREEN API (мессенджер MAX).

Документация: https://green-api.com/docs/
Эндпоинт построен по шаблону:
    {apiUrl}/maxInstance{idInstance}/{method}/{apiTokenInstance}

Для WhatsApp путь начинается с `waInstance`, для MAX — `maxInstance`.
Структура методов сохранена единой.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class GreenApiConfig:
    id_instance: str
    api_token: str
    api_url: str = "https://api.green-api.com"
    instance_prefix: str = "maxInstance"  # для MAX мессенджера
    timeout: int = 20


class GreenApiError(Exception):
    pass


class GreenApiClient:
    def __init__(self, config: GreenApiConfig):
        self.config = config

    # ---------- helpers ----------

    def _url(self, method: str) -> str:
        c = self.config
        return f"{c.api_url.rstrip('/')}/{c.instance_prefix}{c.id_instance}/{method}/{c.api_token}"

    @staticmethod
    def normalize_phone(raw: str) -> str:
        """Превращает произвольный номер в chatId формата `<digits>@c.us`."""
        if raw is None:
            raise GreenApiError("Пустой номер телефона")
        s = str(raw).strip()
        if "@" in s:
            return s
        digits = re.sub(r"\D", "", s)
        if not digits:
            raise GreenApiError(f"Не удалось распознать номер: {raw!r}")
        # 8XXXXXXXXXX -> 7XXXXXXXXXX
        if len(digits) == 11 and digits.startswith("8"):
            digits = "7" + digits[1:]
        return f"{digits}@c.us"

    @staticmethod
    def normalize_group_id(raw: str) -> str:
        s = str(raw).strip()
        if "@" in s:
            return s
        return f"{s}@g.us"

    # ---------- API methods ----------

    def get_state_instance(self) -> dict:
        r = requests.get(self._url("getStateInstance"), timeout=self.config.timeout)
        if not r.ok:
            raise GreenApiError(f"HTTP {r.status_code}: {r.text}")
        return r.json()

    def get_group_data(self, group_id: str) -> dict:
        url = self._url("getGroupData")
        r = requests.post(
            url,
            json={"groupId": self.normalize_group_id(group_id)},
            timeout=self.config.timeout,
        )
        if not r.ok:
            raise GreenApiError(f"HTTP {r.status_code}: {r.text}")
        return r.json()

    def add_group_participant(self, group_id: str, phone: str) -> dict:
        url = self._url("addGroupParticipant")
        payload = {
            "groupId": self.normalize_group_id(group_id),
            "participantChatId": self.normalize_phone(phone),
        }
        r = requests.post(url, json=payload, timeout=self.config.timeout)
        try:
            data = r.json()
        except ValueError:
            data = {"raw": r.text}
        if not r.ok:
            raise GreenApiError(f"HTTP {r.status_code}: {data}")
        return data

"""HTTP-клиент GREEN API для мессенджера MAX.

Зелёное API использует per-instance host: `https://{xxxx}.api.green-api.com`,
где `xxxx` — первые 4 цифры `idInstance`. Префикс пути для всех инстансов —
`waInstance` (это нотация самого API, не зависит от мессенджера).

Эндпоинт:
    {apiUrl}/waInstance{idInstance}/{method}/{apiTokenInstance}

Если `api_url` не задан (или указан как корневой `https://api.green-api.com`),
он достраивается до хоста инстанса.

Особенности MAX (отличаются от WhatsApp):
  * groupId — голая числовая строка вида "-74681263834557", без "@g.us".
  * chatId участника — голая числовая строка вида "71006653", без "@c.us".
  * `checkAccount` принимает `phoneNumber` целым числом.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

import requests


_DEFAULT_HOST = "https://api.green-api.com"


@dataclass
class GreenApiConfig:
    id_instance: str
    api_token: str
    api_url: str = ""               # пусто → авто по id_instance
    instance_prefix: str = "waInstance"
    timeout: int = 20

    def resolved_api_url(self) -> str:
        url = (self.api_url or "").strip().rstrip("/")
        digits = "".join(ch for ch in self.id_instance if ch.isdigit())
        if (not url or url == _DEFAULT_HOST) and len(digits) >= 4:
            return f"https://{digits[:4]}.api.green-api.com"
        return url or _DEFAULT_HOST


class GreenApiError(Exception):
    pass


# ---------- хелперы нормализации ----------

def phone_digits(raw: Any) -> str:
    """Возвращает только цифры из произвольной строки телефона.

    Конвертирует `8XXXXXXXXXX` → `7XXXXXXXXXX` (российская локальная запись).
    Бросает GreenApiError, если цифр нет.
    """
    if raw is None or str(raw).strip() == "":
        raise GreenApiError("Пустой номер телефона")
    digits = re.sub(r"\D", "", str(raw))
    if not digits:
        raise GreenApiError(f"Не удалось распознать номер: {raw!r}")
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


def normalize_group_id(raw: Any) -> str:
    """MAX-формат: голая строка ID. Возвращаем как есть, только без пробелов."""
    s = str(raw or "").strip()
    if not s:
        raise GreenApiError("Пустой groupId")
    return s


# ---------- клиент ----------

class GreenApiClient:
    def __init__(self, config: GreenApiConfig):
        self.config = config

    # обратная совместимость с прежними импортами / view-кодом
    normalize_phone = staticmethod(phone_digits)
    normalize_group_id = staticmethod(normalize_group_id)

    def _url(self, method: str) -> str:
        c = self.config
        host = c.resolved_api_url()
        return f"{host}/{c.instance_prefix}{c.id_instance}/{method}/{c.api_token}"

    def _post(self, method: str, payload: dict) -> dict:
        r = requests.post(self._url(method), json=payload, timeout=self.config.timeout)
        try:
            data = r.json()
        except ValueError:
            data = {"raw": r.text}
        if not r.ok:
            raise GreenApiError(f"HTTP {r.status_code} {method}: {data}")
        return data

    def _get(self, method: str) -> dict:
        r = requests.get(self._url(method), timeout=self.config.timeout)
        try:
            data = r.json()
        except ValueError:
            data = {"raw": r.text}
        if not r.ok:
            raise GreenApiError(f"HTTP {r.status_code} {method}: {data}")
        return data

    # ---------- методы API ----------

    def get_state_instance(self) -> dict:
        return self._get("getStateInstance")

    def get_group_data(self, group_id: str) -> dict:
        return self._post("getGroupData", {"chatId": normalize_group_id(group_id)})

    def check_account(self, phone: str) -> dict:
        """`phoneNumber` отправляется целым числом, как в доке Green-API."""
        digits = phone_digits(phone)
        try:
            phone_int = int(digits)
        except ValueError:  # pragma: no cover
            raise GreenApiError(f"Некорректный номер: {phone!r}")
        return self._post("checkAccount", {"phoneNumber": phone_int})

    def add_group_participant(
        self,
        group_id: str,
        phone: Optional[str] = None,
        *,
        participant_chat_id: Optional[str] = None,
    ) -> dict:
        """Добавляет участника в групповой чат MAX.

        Можно передать либо `phone` (он будет нормализован в чистые цифры),
        либо явный `participant_chat_id` (если он уже получен, например через
        `checkAccount`).
        """
        if participant_chat_id:
            chat_id = str(participant_chat_id).strip()
        elif phone is not None:
            chat_id = phone_digits(phone)
        else:
            raise GreenApiError("Не указан ни phone, ни participant_chat_id")

        payload = {
            "chatId": normalize_group_id(group_id),
            "participantChatId": chat_id,
        }
        return self._post("addGroupParticipant", payload)

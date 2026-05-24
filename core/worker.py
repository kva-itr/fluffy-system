"""Фоновый воркер пакетного добавления участников в группу."""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import List

from .excel import UserRow
from .green_api import GreenApiClient, GreenApiConfig, GreenApiError


@dataclass
class InviteEvent:
    kind: str          # "log" | "user" | "progress" | "done"
    index: int = -1
    # статусы строки: pending | checking | sending | ok | skipped | error
    status: str = ""
    message: str = ""
    done: int = 0
    total: int = 0
    ok: int = 0
    fail: int = 0
    skipped: int = 0


class InviteWorker:
    def __init__(
        self,
        config: GreenApiConfig,
        group_id: str,
        users: List[UserRow],
        delay: float,
        check_account: bool = True,
    ):
        self.config = config
        self.group_id = group_id
        self.users = users
        self.delay = max(0.0, float(delay))
        self.check_account = bool(check_account)
        self.events: "queue.Queue[InviteEvent]" = queue.Queue()
        self.stop_flag = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.stop_flag.set()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _emit(self, ev: InviteEvent) -> None:
        self.events.put(ev)

    def _run(self) -> None:
        client = GreenApiClient(self.config)
        total = len(self.users)
        ok = 0
        fail = 0
        skipped = 0

        self._emit(InviteEvent(
            kind="log",
            message=(
                f"Старт. Группа: {self.group_id}. Получателей: {total}. "
                f"Предпроверка checkAccount: {'да' if self.check_account else 'нет'}."
            ),
        ))

        for i, user in enumerate(self.users):
            if self.stop_flag.is_set():
                self._emit(InviteEvent(kind="log", message="Остановлено пользователем."))
                break

            try:
                phone_digits = GreenApiClient.normalize_phone(user.phone)

                chat_id_hint: str | None = None
                if self.check_account:
                    self._emit(InviteEvent(kind="user", index=i, status="checking"))
                    check = client.check_account(user.phone)
                    if not _account_exists(check):
                        skipped += 1
                        self._emit(InviteEvent(kind="user", index=i, status="skipped",
                                               message="нет аккаунта MAX"))
                        self._emit(InviteEvent(
                            kind="log",
                            message=f"[{i+1}/{total}] {user.name} · {phone_digits} — пропущен: нет аккаунта MAX. ({check})",
                        ))
                        self._emit(InviteEvent(kind="progress", done=i + 1, total=total))
                        if i + 1 < total and not self.stop_flag.is_set():
                            time.sleep(self.delay)
                        continue
                    chat_id_hint = _extract_chat_id(check)

                self._emit(InviteEvent(kind="user", index=i, status="sending"))
                result = client.add_group_participant(
                    self.group_id,
                    phone=user.phone,
                    participant_chat_id=chat_id_hint,
                )
                added = result.get("addParticipant", result.get("result", True))
                if added is False:
                    raise GreenApiError(f"API вернул отказ: {result}")
                ok += 1
                self._emit(InviteEvent(kind="user", index=i, status="ok"))
                self._emit(InviteEvent(
                    kind="log",
                    message=f"[{i+1}/{total}] {user.name} · {phone_digits} — добавлен.",
                ))
            except Exception as e:
                fail += 1
                self._emit(InviteEvent(kind="user", index=i, status="error", message=str(e)))
                self._emit(InviteEvent(
                    kind="log",
                    message=f"[{i+1}/{total}] {user.name} · {user.phone} — ошибка: {e}",
                ))

            self._emit(InviteEvent(kind="progress", done=i + 1, total=total))

            if i + 1 < total and not self.stop_flag.is_set():
                time.sleep(self.delay)

        self._emit(InviteEvent(kind="done", ok=ok, fail=fail, skipped=skipped, total=total))


# ---------- helpers ----------

def _account_exists(response: dict) -> bool:
    """Универсальный парсер ответа checkAccount.

    Доступные у Green-API ключи зависят от продукта (MAX/WhatsApp). Поддерживаем
    распространённые варианты: existsWhatsapp, existsMax, exists, ok, result.
    """
    if not isinstance(response, dict):
        return False
    for key in ("existsMax", "existsWhatsapp", "exists", "ok", "result"):
        if key in response:
            return bool(response[key])
    return False


def _extract_chat_id(response: dict) -> str | None:
    """Если API вернул chatId аккаунта — извлечь, иначе None."""
    if not isinstance(response, dict):
        return None
    for key in ("chatId", "id", "accountId"):
        v = response.get(key)
        if isinstance(v, (str, int)) and str(v).strip():
            return str(v).strip()
    return None

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
    status: str = ""   # "pending" | "sending" | "ok" | "error"
    message: str = ""
    done: int = 0
    total: int = 0
    ok: int = 0
    fail: int = 0


class InviteWorker:
    def __init__(
        self,
        config: GreenApiConfig,
        group_id: str,
        users: List[UserRow],
        delay: float,
    ):
        self.config = config
        self.group_id = group_id
        self.users = users
        self.delay = max(0.0, float(delay))
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

        self._emit(InviteEvent(
            kind="log",
            message=f"Старт. Группа: {self.group_id}. Получателей: {total}.",
        ))

        for i, user in enumerate(self.users):
            if self.stop_flag.is_set():
                self._emit(InviteEvent(kind="log", message="Остановлено пользователем."))
                break

            self._emit(InviteEvent(kind="user", index=i, status="sending"))

            try:
                phone_norm = GreenApiClient.normalize_phone(user.phone)
                result = client.add_group_participant(self.group_id, user.phone)
                added = result.get("addParticipant", result.get("result", True))
                if added is False:
                    raise GreenApiError(f"API вернул отказ: {result}")
                ok += 1
                self._emit(InviteEvent(kind="user", index=i, status="ok"))
                self._emit(InviteEvent(
                    kind="log",
                    message=f"[{i+1}/{total}] {user.name} · {phone_norm} — добавлен.",
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

        self._emit(InviteEvent(kind="done", ok=ok, fail=fail, total=total))

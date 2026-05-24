"""Шаг 2 — учётные данные GREEN API и проверка подключения."""

from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk

from core import GreenApiClient, GreenApiConfig, GreenApiError

from .. import theme as T
from ..components import (
    FieldRow,
    Heading,
    Pill,
    PrimaryButton,
    SecondaryButton,
    Subtitle,
)
from ._base import BaseView


class ConnectionView(BaseView):
    def build(self) -> None:
        Heading(self.body, "Подключение к GREEN API", level="title").grid(
            row=0, column=0, sticky="ew",
        )
        Subtitle(
            self.body,
            "Данные инстанса можно скопировать в личном кабинете GREEN API. "
            "Токен хранится локально и нигде не передаётся.",
        ).grid(row=1, column=0, sticky="ew", pady=(T.SP_2, T.SP_5))

        # Сетка полей 2x2
        grid = ctk.CTkFrame(self.body, fg_color="transparent")
        grid.grid(row=2, column=0, sticky="nsew")
        grid.grid_columnconfigure((0, 1), weight=1, uniform="fields")

        s = self.state.settings

        self.f_id = FieldRow(grid, "ID инстанса", "1101000001",
                             hint="Поле idInstance из кабинета GREEN API.")
        self.f_id.grid(row=0, column=0, sticky="ew", padx=(0, T.SP_3), pady=(0, T.SP_4))
        self.f_id.set(s.id_instance)

        self.f_token = FieldRow(grid, "API Token", "•••••••• • • •",
                                show="•",
                                hint="Поле apiTokenInstance. Хранится только на этом устройстве.")
        self.f_token.grid(row=0, column=1, sticky="ew", padx=(T.SP_3, 0), pady=(0, T.SP_4))
        self.f_token.set(s.api_token)

        self.f_url = FieldRow(
            grid, "API URL (необязательно)",
            "авто: https://{xxxx}.api.green-api.com",
            hint=(
                "Можно оставить пустым — хост подставится по первым 4 цифрам "
                "ID инстанса. Заполняйте, только если личный кабинет показывает "
                "другой адрес."
            ),
        )
        self.f_url.grid(row=1, column=0, sticky="ew", padx=(0, T.SP_3))
        self.f_url.set(s.api_url)

        self.f_delay = FieldRow(grid, "Задержка между запросами, сек.", "1.5",
                                hint="Рекомендуется ≥ 1.5 с, чтобы не упереться в лимиты API.")
        self.f_delay.grid(row=1, column=1, sticky="ew", padx=(T.SP_3, 0))
        self.f_delay.set(str(s.delay))

        # Статус-пилюля
        status = ctk.CTkFrame(self.body, fg_color="transparent")
        status.grid(row=3, column=0, sticky="ew", pady=(T.SP_5, 0))
        self.status_pill = Pill(status, text="не проверено", variant="neutral")
        self.status_pill.pack(side="left")
        self.status_text = ctk.CTkLabel(
            status, text="",
            font=T.typography.caption(),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        )
        self.status_text.pack(side="left", padx=(T.SP_3, 0))

        # Если в state уже есть результат проверки — отрисуем
        if self.state.instance_state:
            self._set_status("success", "Подключение успешно проверено")

        # Футер
        SecondaryButton(self.footer.left, text="←  Назад", width=140,
                        command=self.go_back).pack(side="left")

        SecondaryButton(self.footer.right, text="Проверить", width=160,
                        command=self.on_check).pack(side="left", padx=(0, T.SP_3))
        PrimaryButton(self.footer.right, text="Далее  →", width=160,
                      command=self.on_next).pack(side="left")

    # ---------- helpers ----------

    def _save(self) -> None:
        s = self.state.settings
        s.id_instance = self.f_id.get()
        s.api_token = self.f_token.get()
        s.api_url = self.f_url.get()  # пусто допустимо — авто-хост
        try:
            s.delay = float(self.f_delay.get().replace(",", "."))
        except ValueError:
            s.delay = 1.5
        self.persist()

    def _set_status(self, variant: str, text: str) -> None:
        labels = {
            "neutral": "не проверено",
            "accent": "проверка…",
            "success": "подключено",
            "danger": "ошибка",
        }
        self.status_pill.set_variant(variant, labels.get(variant, text))
        self.status_text.configure(text=text)

    def on_check(self) -> None:
        self._save()
        s = self.state.settings
        if not s.id_instance or not s.api_token:
            messagebox.showwarning("Внимание", "Заполните ID инстанса и API Token.")
            return
        self._set_status("accent", "Отправляем getStateInstance…")

        def task():
            try:
                cfg = GreenApiConfig(s.id_instance, s.api_token, s.api_url)
                result = GreenApiClient(cfg).get_state_instance()
                self.state.instance_state = result
                state_value = result.get("stateInstance", str(result))
                self.after(0, lambda: self._set_status(
                    "success" if state_value == "authorized" else "warn",
                    f"Состояние: {state_value}",
                ))
            except Exception as e:
                self.after(0, lambda: self._set_status("danger", str(e)))

        threading.Thread(target=task, daemon=True).start()

    def on_next(self) -> None:
        self._save()
        s = self.state.settings
        if not s.id_instance or not s.api_token:
            messagebox.showwarning("Внимание", "Заполните ID инстанса и API Token.")
            return
        self.go_next()

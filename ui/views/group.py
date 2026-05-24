"""Шаг 3 — указание ID группы и проверка её данных."""

from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk

from core import GreenApiClient, GreenApiConfig

from .. import theme as T
from ..components import (
    FieldRow,
    Heading,
    InsetSurface,
    Pill,
    PrimaryButton,
    SecondaryButton,
    Subtitle,
)
from ._base import BaseView


class GroupView(BaseView):
    def build(self) -> None:
        Heading(self.body, "Куда добавляем", level="title").grid(
            row=0, column=0, sticky="ew",
        )
        Subtitle(
            self.body,
            "Укажите ID групповой беседы MAX. ID можно получить методом "
            "getChats / в свойствах группы. Кнопка «Получить данные» подтянет "
            "название и количество участников.",
        ).grid(row=1, column=0, sticky="ew", pady=(T.SP_2, T.SP_5))

        self.f_group = FieldRow(
            self.body, "ID группы",
            placeholder="120363025246125888",
            hint="Можно указать без суффикса @g.us — мы добавим его автоматически.",
        )
        self.f_group.grid(row=2, column=0, sticky="ew")
        self.f_group.set(self.state.settings.group_id)

        # Кнопка проверки
        actions = ctk.CTkFrame(self.body, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", pady=(T.SP_4, T.SP_5))
        actions.grid_columnconfigure(0, weight=1)

        self.status_pill = Pill(actions, text="не проверено", variant="neutral")
        self.status_pill.grid(row=0, column=0, sticky="w")
        SecondaryButton(actions, text="Получить данные группы", width=240,
                        command=self.on_fetch).grid(row=0, column=1, sticky="e")

        # Карточка превью
        self.preview = InsetSurface(self.body)
        self.preview.grid(row=4, column=0, sticky="ew")
        self._render_preview(self.state.group_info)

        # Футер
        SecondaryButton(self.footer.left, text="←  Назад", width=140,
                        command=self.go_back).pack(side="left")
        PrimaryButton(self.footer.right, text="Далее  →", width=180,
                      command=self.on_next).pack()

    # ---------- helpers ----------

    def _save(self) -> None:
        self.state.settings.group_id = self.f_group.get()
        self.persist()

    def _set_status(self, variant: str, label: str) -> None:
        self.status_pill.set_variant(variant, label)

    def _render_preview(self, info: dict | None) -> None:
        for child in self.preview.winfo_children():
            child.destroy()

        if not info:
            placeholder = ctk.CTkLabel(
                self.preview,
                text="Данные группы появятся здесь после проверки.",
                font=T.typography.body(),
                text_color=T.TEXT_TERTIARY,
                anchor="w",
            )
            placeholder.pack(fill="x", padx=T.SP_5, pady=T.SP_5)
            return

        wrap = ctk.CTkFrame(self.preview, fg_color="transparent")
        wrap.pack(fill="x", padx=T.SP_5, pady=T.SP_5)
        wrap.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            wrap, text="👥", width=56, height=56,
            corner_radius=14, fg_color=T.ACCENT_SOFT,
            text_color=T.ACCENT,
            font=(T.typography.family, 26),
        ).grid(row=0, column=0, rowspan=2, padx=(0, T.SP_4))

        name = info.get("subject") or info.get("groupName") or "Без названия"
        ctk.CTkLabel(
            wrap, text=name, anchor="w",
            font=T.typography.section(), text_color=T.TEXT_PRIMARY,
        ).grid(row=0, column=1, sticky="ew")

        # Метаданные
        meta_parts = []
        participants = info.get("participants")
        if isinstance(participants, list):
            meta_parts.append(f"{len(participants)} участников")
        if "owner" in info:
            meta_parts.append(f"Владелец: {info['owner']}")
        if "creation" in info:
            meta_parts.append(f"Создана: {info['creation']}")
        ctk.CTkLabel(
            wrap, text="  ·  ".join(meta_parts) or "Метаданные недоступны",
            anchor="w",
            font=T.typography.caption(),
            text_color=T.TEXT_SECONDARY,
        ).grid(row=1, column=1, sticky="ew", pady=(2, 0))

    def on_fetch(self) -> None:
        self._save()
        s = self.state.settings
        if not s.group_id:
            messagebox.showwarning("Внимание", "Укажите ID группы.")
            return
        if not s.id_instance or not s.api_token:
            messagebox.showwarning("Внимание",
                                   "Сначала заполните учётные данные на шаге «Подключение».")
            return

        self._set_status("accent", "запрос…")

        def task():
            try:
                cfg = GreenApiConfig(s.id_instance, s.api_token, s.api_url)
                info = GreenApiClient(cfg).get_group_data(s.group_id)
                self.state.group_info = info
                self.after(0, lambda: (
                    self._render_preview(info),
                    self._set_status("success", "данные получены"),
                ))
            except Exception as e:
                self.after(0, lambda: (
                    self._set_status("danger", "ошибка"),
                    messagebox.showerror("Ошибка", str(e)),
                ))

        threading.Thread(target=task, daemon=True).start()

    def on_next(self) -> None:
        self._save()
        if not self.state.settings.group_id:
            messagebox.showwarning("Внимание", "Укажите ID группы.")
            return
        self.go_next()

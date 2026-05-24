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
            "Укажите ID групповой беседы MAX. Это голая числовая строка вида "
            "«-74681263834557». Кнопка «Получить данные» вызывает getGroupData "
            "и показывает название, владельца, дату создания и количество "
            "участников.",
        ).grid(row=1, column=0, sticky="ew", pady=(T.SP_2, T.SP_5))

        self.f_group = FieldRow(
            self.body, "ID группы",
            placeholder="-74681263834557",
            hint="Для MAX это числовой ID без суффикса @g.us.",
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

        # Аватар-плашка
        ctk.CTkLabel(
            wrap, text="👥", width=56, height=56,
            corner_radius=14, fg_color=T.ACCENT_SOFT,
            text_color=T.ACCENT,
            font=(T.typography.family, 26),
        ).grid(row=0, column=0, rowspan=2, padx=(0, T.SP_4), sticky="n")

        # Название
        name = info.get("subject") or info.get("groupName") or "Без названия"
        ctk.CTkLabel(
            wrap, text=name, anchor="w",
            font=T.typography.section(), text_color=T.TEXT_PRIMARY,
        ).grid(row=0, column=1, sticky="ew")

        # Чип-метаданные
        meta = ctk.CTkFrame(wrap, fg_color="transparent")
        meta.grid(row=1, column=1, sticky="ew", pady=(6, 0))

        chips: list[tuple[str, str]] = []

        size = info.get("size")
        participants = info.get("participants")
        if isinstance(size, int):
            chips.append(("УЧАСТНИКОВ", str(size)))
        elif isinstance(participants, list):
            chips.append(("УЧАСТНИКОВ", str(len(participants))))

        chat_id = info.get("chatId") or info.get("groupId")
        if chat_id:
            chips.append(("ID", str(chat_id)))

        owner = info.get("owner")
        if owner:
            chips.append(("ВЛАДЕЛЕЦ", str(owner)))

        creation = info.get("creation")
        if isinstance(creation, (int, float)) and creation > 0:
            try:
                from datetime import datetime
                chips.append(("СОЗДАНА", datetime.fromtimestamp(creation).strftime("%d.%m.%Y")))
            except (ValueError, OSError, OverflowError):
                pass

        if info.get("isOfficial"):
            chips.append(("СТАТУС", "официальная"))

        for i, (label, value) in enumerate(chips):
            chip = ctk.CTkFrame(
                meta, fg_color=T.BG_CARD,
                corner_radius=T.R_SM,
                border_width=1, border_color=T.BORDER,
            )
            chip.grid(row=0, column=i, sticky="w", padx=(0, T.SP_2), pady=(0, T.SP_2))
            ctk.CTkLabel(
                chip, text=label,
                font=T.typography.small(), text_color=T.TEXT_TERTIARY,
            ).pack(anchor="w", padx=10, pady=(4, 0))
            ctk.CTkLabel(
                chip, text=value,
                font=T.typography.caption_bold(), text_color=T.TEXT_PRIMARY,
            ).pack(anchor="w", padx=10, pady=(0, 4))

        description = info.get("description")
        if description:
            ctk.CTkLabel(
                wrap, text=str(description), anchor="w", justify="left",
                font=T.typography.caption(), text_color=T.TEXT_SECONDARY,
                wraplength=560,
            ).grid(row=2, column=1, sticky="ew", pady=(T.SP_3, 0))

        invite = info.get("groupInviteLink")
        if invite:
            ctk.CTkLabel(
                wrap, text=str(invite), anchor="w",
                font=T.typography.code(), text_color=T.ACCENT,
            ).grid(row=3, column=1, sticky="ew", pady=(T.SP_2, 0))

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

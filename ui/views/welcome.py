"""Шаг 1 — приветствие и краткое описание потока."""

from __future__ import annotations

import customtkinter as ctk

from .. import theme as T
from ..components import Heading, PrimaryButton, Subtitle
from ._base import BaseView


HIGHLIGHTS = [
    ("🔐", "Подключение",
     "ID инстанса и токен GREEN API. Проверим связь до старта."),
    ("👥", "Группа",
     "Подтянем название и количество участников по ID группы."),
    ("📊", "Excel",
     "Импорт получателей. Сами найдём колонки и нормализуем номера."),
    ("🚀", "Рассылка",
     "Пакетное добавление с прогрессом, статусами и журналом."),
]


class WelcomeView(BaseView):
    title_text = "Добро пожаловать"

    def build(self) -> None:
        Heading(self.body, "MAX Group Inviter", level="display").grid(
            row=0, column=0, sticky="ew"
        )
        Subtitle(
            self.body,
            "Массовое приглашение участников в группу мессенджера MAX через "
            "GREEN API. Импорт списка из Excel, проверки на каждом шаге, "
            "наглядный прогресс и журнал.",
        ).grid(row=1, column=0, sticky="ew", pady=(T.SP_2, T.SP_5))

        grid = ctk.CTkFrame(self.body, fg_color="transparent")
        grid.grid(row=2, column=0, sticky="nsew", pady=(T.SP_2, 0))
        grid.grid_columnconfigure((0, 1), weight=1, uniform="cards")

        for i, (icon, title, text) in enumerate(HIGHLIGHTS):
            self._build_tile(grid, i // 2, i % 2, icon, title, text)

        # Футер
        PrimaryButton(
            self.footer.right, text="Начать  →", width=180,
            command=self.go_next,
        ).pack()

    def _build_tile(self, parent, row: int, col: int,
                    icon: str, title: str, text: str) -> None:
        tile = ctk.CTkFrame(
            parent,
            fg_color=T.BG_CARD_INSET,
            corner_radius=T.R_MD,
            border_width=1,
            border_color=T.BORDER,
        )
        tile.grid(row=row, column=col, sticky="nsew",
                  padx=(0 if col == 0 else T.SP_3, T.SP_3 if col == 0 else 0),
                  pady=(0, T.SP_3))
        tile.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            tile, text=icon, font=(T.typography.family, 26),
            width=52, height=52, corner_radius=14,
            fg_color=T.BG_CARD, text_color=T.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=(T.SP_4, T.SP_3), pady=T.SP_4)

        inner = ctk.CTkFrame(tile, fg_color="transparent")
        inner.grid(row=0, column=1, sticky="ew", padx=(0, T.SP_4), pady=T.SP_4)
        ctk.CTkLabel(
            inner, text=title, anchor="w",
            font=T.typography.body_bold(), text_color=T.TEXT_PRIMARY,
        ).pack(fill="x")
        ctk.CTkLabel(
            inner, text=text, anchor="w", justify="left",
            font=T.typography.caption(), text_color=T.TEXT_SECONDARY,
            wraplength=320,
        ).pack(fill="x", pady=(2, 0))

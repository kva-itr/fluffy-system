"""Базовый класс view."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .. import theme as T
from ..components import Card, FooterBar


class BaseView(ctk.CTkFrame):
    """Стандартная структура: карточка + футер с навигацией."""

    title_text: str = ""
    subtitle_text: str = ""

    def __init__(
        self,
        master,
        state,
        go_next: Callable[[], None],
        go_back: Callable[[], None],
        persist: Callable[[], None],
    ):
        super().__init__(master, fg_color=T.BG_PAGE, corner_radius=0)
        self.state = state
        self.go_next = go_next
        self.go_back = go_back
        self.persist = persist

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.card = Card(self)
        self.card.grid(row=0, column=0, sticky="nsew")

        self.footer = FooterBar(self)
        self.footer.grid(row=1, column=0, sticky="ew", pady=(T.SP_5, 0))

        self.body = self.card.body()
        self.body.grid_columnconfigure(0, weight=1)
        self.build()

    def build(self) -> None:  # pragma: no cover - переопределяется
        raise NotImplementedError

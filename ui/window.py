"""Главное окно приложения: сайдбар-степпер + поток шагов мастера."""

from __future__ import annotations

import customtkinter as ctk

from core import AppState, load_settings, save_settings

from . import theme as T
from .components import Caption, Stepper
from .views.connection import ConnectionView
from .views.group import GroupView
from .views.send import SendView
from .views.users import UsersView
from .views.welcome import WelcomeView


STEPS = [
    ("Добро пожаловать", "Краткое введение"),
    ("Подключение",      "GREEN API · MAX"),
    ("Группа",           "Выбор и проверка"),
    ("Получатели",       "Импорт из Excel"),
    ("Рассылка",         "Добавление и журнал"),
]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MAX Group Inviter")
        self.geometry("1180x760")
        self.minsize(1040, 680)

        # NB: `self.state` нельзя — это имя занято методом tk.Tk.state()
        self.app_state = AppState(settings=load_settings())
        ctk.set_appearance_mode(self.app_state.settings.appearance)
        ctk.set_default_color_theme("blue")

        self.configure(fg_color=T.BG_PAGE)

        self._build_layout()
        self._views: list = [None] * len(STEPS)
        self._current = 0
        self._show_view(0)

    # ---------- Layout ----------

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=0, minsize=300)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(
            self,
            fg_color=T.BG_SIDEBAR,
            corner_radius=0,
            border_width=0,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(3, weight=1)

        # Брендовый блок
        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=T.SP_6, pady=(T.SP_6, T.SP_5))
        brand.grid_columnconfigure(1, weight=1)

        logo = ctk.CTkLabel(
            brand,
            text="✦",
            width=44,
            height=44,
            corner_radius=12,
            fg_color=T.ACCENT,
            text_color="#FFFFFF",
            font=(T.typography.family, 22, "bold"),
        )
        logo.grid(row=0, column=0, padx=(0, T.SP_3))

        title_frame = ctk.CTkFrame(brand, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            title_frame,
            text="MAX Inviter",
            font=(T.typography.family, 18, "bold"),
            text_color=T.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame,
            text="через GREEN API",
            font=T.typography.small(),
            text_color=T.TEXT_TERTIARY,
            anchor="w",
        ).pack(anchor="w")

        # Тонкий разделитель
        sep = ctk.CTkFrame(sidebar, height=1, fg_color=T.BORDER, corner_radius=0)
        sep.grid(row=1, column=0, sticky="ew", padx=T.SP_6)

        # Степпер
        self.stepper = Stepper(sidebar, STEPS, on_jump=self._jump_to)
        self.stepper.grid(row=2, column=0, sticky="ew", padx=T.SP_6, pady=(T.SP_5, T.SP_5))

        # Низ сайдбара — переключатель темы
        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", padx=T.SP_6, pady=(0, T.SP_5))
        footer.grid_columnconfigure(0, weight=1)

        Caption(footer, text="Оформление").grid(row=0, column=0, sticky="w", pady=(0, 4))
        appearance = ctk.CTkSegmentedButton(
            footer,
            values=["System", "Light", "Dark"],
            command=self._set_appearance,
            font=T.typography.caption_bold(),
        )
        appearance.set(self.app_state.settings.appearance)
        appearance.grid(row=1, column=0, sticky="ew")

    def _build_content(self) -> None:
        wrap = ctk.CTkFrame(self, fg_color=T.BG_PAGE, corner_radius=0)
        wrap.grid(row=0, column=1, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(1, weight=1)

        # Тонкая полоса заголовка
        topbar = ctk.CTkFrame(wrap, fg_color=T.BG_PAGE, corner_radius=0, height=56)
        topbar.grid(row=0, column=0, sticky="ew", padx=T.SP_7, pady=(T.SP_5, 0))
        topbar.grid_columnconfigure(0, weight=1)
        topbar.grid_propagate(False)

        self.crumb_label = ctk.CTkLabel(
            topbar,
            text="",
            font=T.typography.caption_bold(),
            text_color=T.TEXT_TERTIARY,
            anchor="w",
        )
        self.crumb_label.grid(row=0, column=0, sticky="w")

        # Контейнер для текущей карточки шага
        self.content = ctk.CTkFrame(wrap, fg_color=T.BG_PAGE, corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew", padx=T.SP_7, pady=(T.SP_4, T.SP_6))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    # ---------- Навигация ----------

    def _make_view(self, index: int):
        cls = [WelcomeView, ConnectionView, GroupView, UsersView, SendView][index]
        return cls(
            self.content,
            state=self.app_state,
            go_next=self._next,
            go_back=self._back,
            persist=self._persist,
        )

    def _show_view(self, index: int) -> None:
        # уничтожаем старый view, чтобы карточка перерисовалась с актуальным state
        for child in self.content.winfo_children():
            child.destroy()
        view = self._make_view(index)
        view.grid(row=0, column=0, sticky="nsew")
        self._current = index
        self.stepper.set_current(index)
        self.crumb_label.configure(
            text=f"Шаг {index + 1} из {len(STEPS)}  ·  {STEPS[index][0]}",
        )

    def _next(self) -> None:
        if self._current < len(STEPS) - 1:
            self._show_view(self._current + 1)

    def _back(self) -> None:
        if self._current > 0:
            self._show_view(self._current - 1)

    def _jump_to(self, index: int) -> None:
        if 0 <= index < len(STEPS):
            self._show_view(index)

    # ---------- Прочее ----------

    def _set_appearance(self, value: str) -> None:
        ctk.set_appearance_mode(value)
        self.app_state.settings.appearance = value
        self._persist()

    def _persist(self) -> None:
        save_settings(self.app_state.settings)

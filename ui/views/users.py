"""Шаг 4 — загрузка списка пользователей из Excel."""

from __future__ import annotations

import os
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core import load_users, write_sample

from .. import theme as T
from ..components import (
    GhostButton,
    Heading,
    InsetSurface,
    Pill,
    PrimaryButton,
    SecondaryButton,
    Subtitle,
)
from ._base import BaseView


class UsersView(BaseView):
    def build(self) -> None:
        Heading(self.body, "Список получателей", level="title").grid(
            row=0, column=0, sticky="ew",
        )
        Subtitle(
            self.body,
            "Импорт из Excel. Файл может содержать две колонки — «Имя» и «Телефон». "
            "Заголовок необязателен, мы определим колонки автоматически.",
        ).grid(row=1, column=0, sticky="ew", pady=(T.SP_2, T.SP_5))

        # Зона загрузки файла
        drop = ctk.CTkFrame(
            self.body, fg_color=T.BG_CARD_INSET,
            corner_radius=T.R_MD,
            border_width=1, border_color=T.BORDER,
        )
        drop.grid(row=2, column=0, sticky="ew", pady=(0, T.SP_5))
        drop.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            drop, text="📁", width=56, height=56, corner_radius=14,
            fg_color=T.BG_CARD, text_color=T.TEXT_PRIMARY,
            font=(T.typography.family, 24),
        ).grid(row=0, column=0, rowspan=2, padx=(T.SP_4, T.SP_4), pady=T.SP_4)

        self.file_title = ctk.CTkLabel(
            drop, text="Файл не выбран", anchor="w",
            font=T.typography.body_bold(), text_color=T.TEXT_PRIMARY,
        )
        self.file_title.grid(row=0, column=1, sticky="ew", pady=(T.SP_4, 0))

        self.file_meta = ctk.CTkLabel(
            drop, text="Поддерживаются .xlsx, .xlsm, .xls", anchor="w",
            font=T.typography.caption(), text_color=T.TEXT_SECONDARY,
        )
        self.file_meta.grid(row=1, column=1, sticky="ew", pady=(0, T.SP_4))

        actions = ctk.CTkFrame(drop, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, padx=(0, T.SP_4))
        PrimaryButton(actions, text="Выбрать файл…", width=160,
                      command=self.on_open).pack(pady=(0, 6))
        GhostButton(actions, text="Создать шаблон",
                    command=self.on_template).pack()

        # Заголовок таблицы
        head = ctk.CTkFrame(self.body, fg_color="transparent")
        head.grid(row=3, column=0, sticky="ew", pady=(0, T.SP_2))
        head.grid_columnconfigure(0, weight=1)

        self.count_label = ctk.CTkLabel(
            head, text="Получатели", anchor="w",
            font=T.typography.body_bold(), text_color=T.TEXT_PRIMARY,
        )
        self.count_label.grid(row=0, column=0, sticky="w")

        self.status_pill = Pill(head, text="0", variant="neutral")
        self.status_pill.grid(row=0, column=1, sticky="e")

        # Таблица
        table_card = InsetSurface(self.body)
        table_card.grid(row=4, column=0, sticky="nsew")
        self.body.grid_rowconfigure(4, weight=1)

        self.table = ctk.CTkScrollableFrame(
            table_card, fg_color="transparent",
            label_text="",
        )
        self.table.pack(fill="both", expand=True, padx=T.SP_3, pady=T.SP_3)
        self.table.grid_columnconfigure(0, weight=0)
        self.table.grid_columnconfigure(1, weight=3)
        self.table.grid_columnconfigure(2, weight=2)

        self._render_users()

        # Футер
        SecondaryButton(self.footer.left, text="←  Назад", width=140,
                        command=self.go_back).pack(side="left")
        PrimaryButton(self.footer.right, text="К рассылке  →", width=200,
                      command=self.on_next).pack()

    # ---------- table ----------

    def _render_users(self) -> None:
        for w in self.table.winfo_children():
            w.destroy()

        # header
        for col, text in enumerate(["#", "Имя", "Телефон"]):
            ctk.CTkLabel(
                self.table, text=text,
                font=T.typography.caption_bold(),
                text_color=T.TEXT_TERTIARY, anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=T.SP_3, pady=(T.SP_2, T.SP_3))

        users = self.state.users
        self.status_pill.set_variant(
            "success" if users else "neutral",
            f"{len(users)} в списке" if users else "пусто",
        )
        self.count_label.configure(text=f"Получатели  ({len(users)})")

        if not users:
            ctk.CTkLabel(
                self.table,
                text="Список пуст. Выберите Excel-файл, чтобы загрузить получателей.",
                font=T.typography.body(), text_color=T.TEXT_TERTIARY,
                anchor="w",
            ).grid(row=1, column=0, columnspan=3, sticky="ew",
                   padx=T.SP_3, pady=T.SP_5)
            return

        for i, u in enumerate(users, start=1):
            ctk.CTkLabel(
                self.table, text=str(i),
                font=T.typography.caption(), text_color=T.TEXT_TERTIARY,
                anchor="w",
            ).grid(row=i, column=0, sticky="ew", padx=T.SP_3, pady=4)
            ctk.CTkLabel(
                self.table, text=u.name,
                font=T.typography.body(), text_color=T.TEXT_PRIMARY,
                anchor="w",
            ).grid(row=i, column=1, sticky="ew", padx=T.SP_3, pady=4)
            ctk.CTkLabel(
                self.table, text=u.phone,
                font=T.typography.code(), text_color=T.TEXT_SECONDARY,
                anchor="w",
            ).grid(row=i, column=2, sticky="ew", padx=T.SP_3, pady=4)

    # ---------- handlers ----------

    def on_open(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите Excel-файл со списком получателей",
            filetypes=[("Excel files", "*.xlsx *.xlsm *.xls"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.state.users = load_users(path)
            self.state.excel_path = path
        except Exception as e:
            messagebox.showerror("Ошибка чтения Excel", str(e))
            return
        self.file_title.configure(text=os.path.basename(path))
        self.file_meta.configure(text=f"{len(self.state.users)} строк · {path}")
        self._render_users()

    def on_template(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Сохранить шаблон Excel",
            defaultextension=".xlsx",
            initialfile="users_template.xlsx",
            filetypes=[("Excel files", "*.xlsx")],
        )
        if not path:
            return
        try:
            write_sample(path)
            messagebox.showinfo("Готово", f"Шаблон создан:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def on_next(self) -> None:
        if not self.state.users:
            messagebox.showwarning("Внимание", "Загрузите Excel-файл с получателями.")
            return
        self.go_next()

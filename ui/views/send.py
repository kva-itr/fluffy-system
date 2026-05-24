"""Шаг 5 — пакетная рассылка с прогрессом и журналом."""

from __future__ import annotations

import queue
import time
from tkinter import messagebox

import customtkinter as ctk

from core import GreenApiConfig, InviteWorker

from .. import theme as T
from ..components import (
    DangerButton,
    GhostButton,
    Heading,
    InsetSurface,
    Pill,
    PrimaryButton,
    SecondaryButton,
    Subtitle,
)
from ._base import BaseView


STATUS_MAP = {
    "pending":  ("ожидает",  "neutral"),
    "sending":  ("отправка", "accent"),
    "ok":       ("добавлен", "success"),
    "error":    ("ошибка",   "danger"),
}


class SendView(BaseView):
    def build(self) -> None:
        self.worker: InviteWorker | None = None
        self._user_pills: list[Pill] = []

        Heading(self.body, "Рассылка", level="title").grid(
            row=0, column=0, sticky="ew",
        )

        # Сводка
        summary = self._build_summary()
        summary.grid(row=1, column=0, sticky="ew", pady=(T.SP_2, T.SP_5))

        # Полоса прогресса
        progress_card = ctk.CTkFrame(self.body, fg_color="transparent")
        progress_card.grid(row=2, column=0, sticky="ew", pady=(0, T.SP_4))
        progress_card.grid_columnconfigure(0, weight=1)

        self.progress = ctk.CTkProgressBar(
            progress_card, height=10, corner_radius=5,
            fg_color=T.BG_CARD_INSET, progress_color=T.ACCENT,
        )
        self.progress.set(0)
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, T.SP_3))

        self.progress_label = ctk.CTkLabel(
            progress_card, text=f"0 / {len(self.state.users)}",
            font=T.typography.caption_bold(),
            text_color=T.TEXT_SECONDARY,
        )
        self.progress_label.grid(row=0, column=1, sticky="e")

        # Содержимое: список + журнал
        cols = ctk.CTkFrame(self.body, fg_color="transparent")
        cols.grid(row=3, column=0, sticky="nsew")
        cols.grid_columnconfigure(0, weight=3, uniform="cols")
        cols.grid_columnconfigure(1, weight=2, uniform="cols")
        cols.grid_rowconfigure(0, weight=1)
        self.body.grid_rowconfigure(3, weight=1)

        # — Список получателей со статусами
        list_card = InsetSurface(cols)
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, T.SP_3))
        self.users_scroll = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent", label_text="",
        )
        self.users_scroll.pack(fill="both", expand=True, padx=T.SP_3, pady=T.SP_3)
        self.users_scroll.grid_columnconfigure(1, weight=1)
        self.users_scroll.grid_columnconfigure(2, weight=2)
        self._render_users()

        # — Журнал
        log_card = InsetSurface(cols)
        log_card.grid(row=0, column=1, sticky="nsew", padx=(T.SP_3, 0))
        log_head = ctk.CTkFrame(log_card, fg_color="transparent")
        log_head.pack(fill="x", padx=T.SP_4, pady=(T.SP_3, 0))
        ctk.CTkLabel(
            log_head, text="Журнал",
            font=T.typography.caption_bold(),
            text_color=T.TEXT_TERTIARY,
        ).pack(side="left")
        GhostButton(log_head, text="Очистить",
                    command=self._clear_log).pack(side="right")

        self.log = ctk.CTkTextbox(
            log_card, height=240,
            font=T.typography.code(),
            text_color=T.TEXT_PRIMARY,
            fg_color="transparent",
            border_width=0,
            wrap="word",
        )
        self.log.pack(fill="both", expand=True, padx=T.SP_4, pady=T.SP_4)
        self.log.configure(state="disabled")

        # Футер
        SecondaryButton(self.footer.left, text="←  Назад", width=140,
                        command=self.go_back).pack(side="left")
        self.btn_stop = DangerButton(self.footer.right, text="Остановить",
                                     width=140, command=self.on_stop)
        self.btn_stop.pack(side="left", padx=(0, T.SP_3))
        self.btn_stop.configure(state="disabled")
        self.btn_start = PrimaryButton(self.footer.right, text="🚀  Начать рассылку",
                                       width=220, command=self.on_start)
        self.btn_start.pack(side="left")

    # ---------- summary ----------

    def _build_summary(self) -> ctk.CTkFrame:
        s = self.state.settings
        info = self.state.group_info or {}
        group_name = info.get("subject") or info.get("groupName") or s.group_id or "—"
        total_recipients = len(self.state.users)

        wrap = ctk.CTkFrame(self.body, fg_color="transparent")
        wrap.grid_columnconfigure((0, 1, 2), weight=1, uniform="sm")

        for i, (label, value, accent) in enumerate([
            ("Группа",       group_name,                False),
            ("Получателей",  str(total_recipients),     True),
            ("Задержка",     f"{s.delay:g} сек.",       False),
        ]):
            tile = ctk.CTkFrame(
                wrap, fg_color=T.BG_CARD_INSET,
                corner_radius=T.R_MD, border_width=1, border_color=T.BORDER,
            )
            tile.grid(row=0, column=i, sticky="ew",
                      padx=(0 if i == 0 else T.SP_3, 0))
            ctk.CTkLabel(
                tile, text=label.upper(),
                font=T.typography.small(), text_color=T.TEXT_TERTIARY,
                anchor="w",
            ).pack(fill="x", padx=T.SP_4, pady=(T.SP_3, 0))
            ctk.CTkLabel(
                tile, text=value,
                font=T.typography.section(),
                text_color=T.ACCENT if accent else T.TEXT_PRIMARY,
                anchor="w", justify="left",
                wraplength=240,
            ).pack(fill="x", padx=T.SP_4, pady=(2, T.SP_3))

        return wrap

    # ---------- users list ----------

    def _render_users(self) -> None:
        for w in self.users_scroll.winfo_children():
            w.destroy()
        self._user_pills = []

        ctk.CTkLabel(self.users_scroll, text="#",
                     font=T.typography.caption_bold(),
                     text_color=T.TEXT_TERTIARY, anchor="w"
                     ).grid(row=0, column=0, sticky="ew", padx=T.SP_3, pady=(T.SP_2, T.SP_3))
        ctk.CTkLabel(self.users_scroll, text="Имя · Телефон",
                     font=T.typography.caption_bold(),
                     text_color=T.TEXT_TERTIARY, anchor="w"
                     ).grid(row=0, column=1, sticky="ew", padx=T.SP_3, pady=(T.SP_2, T.SP_3))
        ctk.CTkLabel(self.users_scroll, text="Статус",
                     font=T.typography.caption_bold(),
                     text_color=T.TEXT_TERTIARY, anchor="w"
                     ).grid(row=0, column=2, sticky="ew", padx=T.SP_3, pady=(T.SP_2, T.SP_3))

        for i, u in enumerate(self.state.users, start=1):
            ctk.CTkLabel(
                self.users_scroll, text=str(i), anchor="w",
                font=T.typography.caption(), text_color=T.TEXT_TERTIARY,
            ).grid(row=i, column=0, sticky="ew", padx=T.SP_3, pady=3)

            person = ctk.CTkFrame(self.users_scroll, fg_color="transparent")
            person.grid(row=i, column=1, sticky="ew", padx=T.SP_3, pady=3)
            ctk.CTkLabel(
                person, text=u.name, anchor="w",
                font=T.typography.body(), text_color=T.TEXT_PRIMARY,
            ).pack(fill="x")
            ctk.CTkLabel(
                person, text=u.phone, anchor="w",
                font=T.typography.code(), text_color=T.TEXT_TERTIARY,
            ).pack(fill="x", pady=(1, 0))

            pill = Pill(self.users_scroll, text="ожидает", variant="neutral")
            pill.grid(row=i, column=2, sticky="w", padx=T.SP_3, pady=3)
            self._user_pills.append(pill)

    # ---------- log ----------

    def _log(self, message: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert("end", f"[{ts}]  {message}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    # ---------- handlers ----------

    def on_start(self) -> None:
        if not self.state.users:
            messagebox.showwarning("Внимание",
                                   "Список получателей пуст — вернитесь к предыдущему шагу.")
            return
        s = self.state.settings
        if not s.id_instance or not s.api_token or not s.group_id:
            messagebox.showwarning("Внимание",
                                   "Не заполнены данные подключения или ID группы.")
            return
        if not messagebox.askyesno(
            "Подтверждение",
            f"Добавить {len(self.state.users)} получателей в группу?",
        ):
            return

        cfg = GreenApiConfig(s.id_instance, s.api_token, s.api_url)
        self.worker = InviteWorker(
            config=cfg,
            group_id=s.group_id,
            users=self.state.users,
            delay=s.delay,
        )
        self.worker.start()

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress.set(0)
        self.progress_label.configure(text=f"0 / {len(self.state.users)}")
        self._poll()

    def on_stop(self) -> None:
        if self.worker:
            self.worker.stop()
            self._log("⏸ Запрошена остановка…")

    def _poll(self) -> None:
        if not self.worker:
            return
        try:
            while True:
                ev = self.worker.events.get_nowait()
                self._handle_event(ev)
        except queue.Empty:
            pass

        if self.worker.is_running() or not self.worker.events.empty():
            self.after(80, self._poll)

    def _handle_event(self, ev) -> None:
        if ev.kind == "log":
            self._log(ev.message)
        elif ev.kind == "user":
            if 0 <= ev.index < len(self._user_pills):
                label, variant = STATUS_MAP.get(ev.status, ("…", "neutral"))
                self._user_pills[ev.index].set_variant(variant, label)
        elif ev.kind == "progress":
            self.progress.set(ev.done / ev.total if ev.total else 0)
            self.progress_label.configure(text=f"{ev.done} / {ev.total}")
        elif ev.kind == "done":
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            self._log(f"✅ Готово. Успешно: {ev.ok}, ошибок: {ev.fail}.")
            messagebox.showinfo(
                "Готово",
                f"Рассылка завершена.\n\nУспешно: {ev.ok}\nОшибок: {ev.fail}",
            )

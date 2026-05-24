"""Десктоп-приложение для массового добавления пользователей в группу
мессенджера MAX через GREEN API.

Запуск:
    pip install -r requirements.txt
    python app.py
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from excel_loader import UserRow, load_users, write_sample
from green_api_client import GreenApiClient, GreenApiConfig, GreenApiError


APP_TITLE = "MAX Group Inviter · GREEN API"
SETTINGS_FILE = Path.home() / ".max_group_inviter.json"

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


# ---------- Утилиты сохранения настроек ----------

def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_settings(data: dict) -> None:
    try:
        SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ---------- Главное окно ----------

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1080x720")
        self.minsize(960, 640)

        self.settings = load_settings()
        self.users: list[UserRow] = []
        self.events: queue.Queue = queue.Queue()
        self.worker: threading.Thread | None = None
        self.stop_flag = threading.Event()

        self._build_ui()
        self._poll_events()

    # ---------- UI ----------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ----- Sidebar -----
        sidebar = ctk.CTkFrame(self, corner_radius=0, width=320)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar,
            text="MAX Group Inviter",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(padx=20, pady=(24, 4), anchor="w")
        ctk.CTkLabel(
            sidebar,
            text="через GREEN API",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray70"),
        ).pack(padx=20, pady=(0, 18), anchor="w")

        # Поля конфигурации
        self._add_label(sidebar, "ID инстанса")
        self.entry_id = ctk.CTkEntry(sidebar, placeholder_text="1101000001")
        self.entry_id.pack(padx=20, fill="x")
        self.entry_id.insert(0, self.settings.get("id_instance", ""))

        self._add_label(sidebar, "API Token")
        self.entry_token = ctk.CTkEntry(sidebar, placeholder_text="••••••••", show="•")
        self.entry_token.pack(padx=20, fill="x")
        self.entry_token.insert(0, self.settings.get("api_token", ""))

        self._add_label(sidebar, "ID группы MAX")
        self.entry_group = ctk.CTkEntry(sidebar, placeholder_text="120363025246125888")
        self.entry_group.pack(padx=20, fill="x")
        self.entry_group.insert(0, self.settings.get("group_id", ""))

        self._add_label(sidebar, "API URL")
        self.entry_url = ctk.CTkEntry(sidebar, placeholder_text="https://api.green-api.com")
        self.entry_url.pack(padx=20, fill="x")
        self.entry_url.insert(0, self.settings.get("api_url", "https://api.green-api.com"))

        self._add_label(sidebar, "Задержка между запросами, сек.")
        self.entry_delay = ctk.CTkEntry(sidebar, placeholder_text="1.5")
        self.entry_delay.pack(padx=20, fill="x")
        self.entry_delay.insert(0, str(self.settings.get("delay", 1.5)))

        # Кнопки сайдбара
        ctk.CTkButton(
            sidebar, text="Проверить подключение",
            command=self.on_check_connection,
        ).pack(padx=20, pady=(20, 6), fill="x")

        ctk.CTkButton(
            sidebar, text="Сохранить настройки",
            fg_color="transparent", border_width=1,
            command=self.on_save_settings,
        ).pack(padx=20, pady=(0, 20), fill="x")

        ctk.CTkLabel(
            sidebar,
            text="Тема:",
            font=ctk.CTkFont(size=12),
        ).pack(padx=20, pady=(10, 0), anchor="w")
        appearance = ctk.CTkOptionMenu(
            sidebar, values=["System", "Light", "Dark"],
            command=lambda v: ctk.set_appearance_mode(v),
        )
        appearance.pack(padx=20, pady=(4, 20), fill="x")

        # ----- Main area -----
        main = ctk.CTkFrame(self, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)
        main.grid_rowconfigure(4, weight=1)

        # Верхняя панель — Excel
        excel_panel = ctk.CTkFrame(main)
        excel_panel.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        excel_panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(excel_panel, text="📂 Excel-файл со списком пользователей",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=14, pady=(12, 6), sticky="w"
        )

        ctk.CTkButton(excel_panel, text="Выбрать файл…", width=140,
                      command=self.on_open_excel).grid(row=1, column=0, padx=(14, 6), pady=(0, 12))
        self.label_file = ctk.CTkLabel(excel_panel, text="Файл не выбран",
                                       anchor="w", text_color=("gray30", "gray70"))
        self.label_file.grid(row=1, column=1, sticky="ew", pady=(0, 12))
        ctk.CTkButton(excel_panel, text="Создать шаблон", width=140,
                      fg_color="transparent", border_width=1,
                      command=self.on_make_template).grid(row=1, column=2, padx=(6, 14), pady=(0, 12))

        # Заголовок таблицы пользователей
        users_header = ctk.CTkFrame(main, fg_color="transparent")
        users_header.grid(row=1, column=0, sticky="ew", padx=20)
        users_header.grid_columnconfigure(0, weight=1)
        self.users_title = ctk.CTkLabel(
            users_header, text="👥 Пользователи (0)",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.users_title.grid(row=0, column=0, sticky="w")

        # Таблица пользователей
        self.users_box = ctk.CTkScrollableFrame(main, label_text="")
        self.users_box.grid(row=2, column=0, sticky="nsew", padx=20, pady=(4, 10))
        self.users_box.grid_columnconfigure(0, weight=0)
        self.users_box.grid_columnconfigure(1, weight=2)
        self.users_box.grid_columnconfigure(2, weight=3)
        self.users_box.grid_columnconfigure(3, weight=2)
        self._render_users_header()

        # Кнопки действий
        actions = ctk.CTkFrame(main, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=20)
        actions.grid_columnconfigure(3, weight=1)

        self.btn_start = ctk.CTkButton(
            actions, text="🚀 Добавить всех в группу",
            height=40, font=ctk.CTkFont(size=14, weight="bold"),
            command=self.on_start,
        )
        self.btn_start.grid(row=0, column=0, padx=(0, 8), pady=8)

        self.btn_stop = ctk.CTkButton(
            actions, text="⏹ Остановить", height=40,
            fg_color="#b53737", hover_color="#8a2727",
            state="disabled",
            command=self.on_stop,
        )
        self.btn_stop.grid(row=0, column=1, padx=8, pady=8)

        self.progress = ctk.CTkProgressBar(actions, height=14)
        self.progress.grid(row=0, column=3, sticky="ew", padx=12, pady=8)
        self.progress.set(0)

        self.progress_label = ctk.CTkLabel(actions, text="0 / 0",
                                           font=ctk.CTkFont(size=12))
        self.progress_label.grid(row=0, column=4, padx=(8, 0), pady=8)

        # Лог
        log_label = ctk.CTkLabel(main, text="📜 Журнал операций",
                                 font=ctk.CTkFont(size=14, weight="bold"))
        log_label.grid(row=4, column=0, sticky="nw", padx=20, pady=(8, 0))

        self.log = ctk.CTkTextbox(main, height=180, font=ctk.CTkFont(family="monospace", size=12))
        self.log.grid(row=5, column=0, sticky="nsew", padx=20, pady=(28, 20))
        self.log.configure(state="disabled")
        main.grid_rowconfigure(5, weight=1)

    def _add_label(self, parent, text: str) -> None:
        ctk.CTkLabel(parent, text=text,
                     font=ctk.CTkFont(size=12),
                     text_color=("gray30", "gray70")).pack(
            padx=20, pady=(12, 2), anchor="w"
        )

    def _render_users_header(self) -> None:
        for w in self.users_box.winfo_children():
            w.destroy()
        for col, text in enumerate(["#", "Имя", "Телефон", "Статус"]):
            lbl = ctk.CTkLabel(
                self.users_box, text=text,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            )
            lbl.grid(row=0, column=col, sticky="ew", padx=8, pady=(2, 6))
        self._user_widgets: list[dict] = []

    def _render_users(self) -> None:
        self._render_users_header()
        for i, u in enumerate(self.users, start=1):
            row = i  # row 0 — header
            ctk.CTkLabel(self.users_box, text=str(i), anchor="w").grid(
                row=row, column=0, sticky="ew", padx=8, pady=2)
            ctk.CTkLabel(self.users_box, text=u.name, anchor="w").grid(
                row=row, column=1, sticky="ew", padx=8, pady=2)
            ctk.CTkLabel(self.users_box, text=u.phone, anchor="w").grid(
                row=row, column=2, sticky="ew", padx=8, pady=2)
            status = ctk.CTkLabel(self.users_box, text="ожидает",
                                  anchor="w", text_color=("gray40", "gray70"))
            status.grid(row=row, column=3, sticky="ew", padx=8, pady=2)
            self._user_widgets.append({"status": status})
        self.users_title.configure(text=f"👥 Пользователи ({len(self.users)})")

    # ---------- Event log ----------

    def _log(self, message: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert("end", f"[{ts}] {message}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _poll_events(self) -> None:
        try:
            while True:
                ev = self.events.get_nowait()
                self._handle_event(ev)
        except queue.Empty:
            pass
        self.after(80, self._poll_events)

    def _handle_event(self, ev: dict) -> None:
        kind = ev.get("kind")
        if kind == "log":
            self._log(ev["message"])
        elif kind == "user_status":
            idx = ev["index"]
            if 0 <= idx < len(self._user_widgets):
                w = self._user_widgets[idx]["status"]
                w.configure(text=ev["text"], text_color=ev.get("color"))
        elif kind == "progress":
            done = ev["done"]
            total = ev["total"]
            self.progress.set(done / total if total else 0)
            self.progress_label.configure(text=f"{done} / {total}")
        elif kind == "done":
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            ok = ev.get("ok", 0)
            fail = ev.get("fail", 0)
            self._log(f"✔ Готово. Успешно: {ok}, ошибок: {fail}.")
            messagebox.showinfo(
                "Готово",
                f"Добавление завершено.\n\nУспешно: {ok}\nОшибок: {fail}",
            )

    # ---------- Handlers ----------

    def _current_config(self) -> GreenApiConfig:
        return GreenApiConfig(
            id_instance=self.entry_id.get().strip(),
            api_token=self.entry_token.get().strip(),
            api_url=self.entry_url.get().strip() or "https://api.green-api.com",
        )

    def on_save_settings(self) -> None:
        data = {
            "id_instance": self.entry_id.get().strip(),
            "api_token": self.entry_token.get().strip(),
            "group_id": self.entry_group.get().strip(),
            "api_url": self.entry_url.get().strip(),
        }
        try:
            data["delay"] = float(self.entry_delay.get().strip().replace(",", "."))
        except ValueError:
            data["delay"] = 1.5
        save_settings(data)
        self._log("Настройки сохранены.")

    def on_check_connection(self) -> None:
        cfg = self._current_config()
        if not cfg.id_instance or not cfg.api_token:
            messagebox.showwarning("Внимание", "Заполните ID инстанса и API Token.")
            return
        self._log("Проверка подключения…")

        def task():
            try:
                state = GreenApiClient(cfg).get_state_instance()
                self.events.put({"kind": "log",
                                 "message": f"Статус инстанса: {state}"})
            except Exception as e:
                self.events.put({"kind": "log",
                                 "message": f"Ошибка подключения: {e}"})

        threading.Thread(target=task, daemon=True).start()

    def on_open_excel(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите Excel-файл со списком пользователей",
            filetypes=[("Excel files", "*.xlsx *.xlsm *.xls"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.users = load_users(path)
        except Exception as e:
            messagebox.showerror("Ошибка чтения Excel", str(e))
            return
        self.label_file.configure(text=os.path.basename(path))
        self._render_users()
        self._log(f"Загружено пользователей: {len(self.users)} из «{os.path.basename(path)}».")

    def on_make_template(self) -> None:
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
            self._log(f"Создан шаблон: {path}")
            messagebox.showinfo("Готово", f"Шаблон создан:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def on_start(self) -> None:
        if not self.users:
            messagebox.showwarning("Внимание", "Сначала загрузите Excel-файл со списком пользователей.")
            return
        cfg = self._current_config()
        group_id = self.entry_group.get().strip()
        if not cfg.id_instance or not cfg.api_token or not group_id:
            messagebox.showwarning("Внимание",
                                   "Заполните ID инстанса, API Token и ID группы.")
            return
        try:
            delay = float(self.entry_delay.get().strip().replace(",", "."))
        except ValueError:
            delay = 1.5

        if not messagebox.askyesno(
            "Подтверждение",
            f"Добавить {len(self.users)} пользователей в группу?\n\nГруппа: {group_id}",
        ):
            return

        self.on_save_settings()
        self.stop_flag.clear()
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress.set(0)
        self.progress_label.configure(text=f"0 / {len(self.users)}")

        self.worker = threading.Thread(
            target=self._run_invite,
            args=(cfg, group_id, delay),
            daemon=True,
        )
        self.worker.start()

    def on_stop(self) -> None:
        self.stop_flag.set()
        self._log("Получен сигнал остановки…")

    # ---------- Worker ----------

    def _run_invite(self, cfg: GreenApiConfig, group_id: str, delay: float) -> None:
        client = GreenApiClient(cfg)
        total = len(self.users)
        ok = 0
        fail = 0

        self.events.put({"kind": "log",
                         "message": f"Начало работы. Группа: {group_id}, пользователей: {total}."})

        for i, user in enumerate(self.users):
            if self.stop_flag.is_set():
                self.events.put({"kind": "log", "message": "Остановлено пользователем."})
                break

            self.events.put({"kind": "user_status", "index": i,
                             "text": "отправка…", "color": ("#1a73e8", "#7ab8ff")})

            try:
                phone_norm = GreenApiClient.normalize_phone(user.phone)
                result = client.add_group_participant(group_id, user.phone)
                added = result.get("addParticipant", result.get("result", True))
                if added is False:
                    raise GreenApiError(f"API вернул отказ: {result}")
                ok += 1
                self.events.put({"kind": "user_status", "index": i,
                                 "text": "✓ добавлен", "color": ("#1e8e3e", "#7fdc97")})
                self.events.put({"kind": "log",
                                 "message": f"[{i+1}/{total}] {user.name} ({phone_norm}) — добавлен."})
            except Exception as e:
                fail += 1
                self.events.put({"kind": "user_status", "index": i,
                                 "text": f"✗ ошибка", "color": ("#b53737", "#ff8a8a")})
                self.events.put({"kind": "log",
                                 "message": f"[{i+1}/{total}] {user.name} ({user.phone}) — ошибка: {e}"})

            self.events.put({"kind": "progress", "done": i + 1, "total": total})

            if i + 1 < total and not self.stop_flag.is_set():
                time.sleep(max(0.0, delay))

        self.events.put({"kind": "done", "ok": ok, "fail": fail})


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()

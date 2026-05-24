"""Переиспользуемые UI-компоненты, построенные поверх CustomTkinter."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from . import theme as T


# ---------- Заголовки ----------

class Heading(ctk.CTkLabel):
    def __init__(self, master, text: str, level: str = "title", **kwargs):
        font_map = {
            "display": T.typography.display(),
            "title": T.typography.title(),
            "section": T.typography.section(),
            "body": T.typography.body_bold(),
        }
        super().__init__(
            master,
            text=text,
            font=font_map.get(level, T.typography.title()),
            text_color=T.TEXT_PRIMARY,
            anchor="w",
            **kwargs,
        )


class Subtitle(ctk.CTkLabel):
    def __init__(self, master, text: str, **kwargs):
        super().__init__(
            master,
            text=text,
            font=T.typography.body(),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=kwargs.pop("wraplength", 560),
            **kwargs,
        )


class Caption(ctk.CTkLabel):
    def __init__(self, master, text: str, **kwargs):
        super().__init__(
            master,
            text=text,
            font=T.typography.caption(),
            text_color=T.TEXT_TERTIARY,
            anchor="w",
            **kwargs,
        )


# ---------- Поверхности ----------

class Card(ctk.CTkFrame):
    """Карточка с радиусом, лёгким контуром и внутренним отступом."""

    def __init__(self, master, padding: int = T.SP_6, **kwargs):
        super().__init__(
            master,
            corner_radius=T.R_LG,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER,
            **kwargs,
        )
        self._padding = padding

    def body(self) -> ctk.CTkFrame:
        """Внутренний контейнер с фиксированным padding."""
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=self._padding, pady=self._padding)
        return inner


class InsetSurface(ctk.CTkFrame):
    """Вложенная «утопленная» поверхность — для таблиц, лога, превью."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=T.R_MD,
            fg_color=T.BG_CARD_INSET,
            border_width=1,
            border_color=T.BORDER,
            **kwargs,
        )


# ---------- Бэйджи / пилюли ----------

class Pill(ctk.CTkLabel):
    """Цветная пилюля-статус."""

    VARIANTS = {
        "neutral": (T.BG_FIELD, T.TEXT_SECONDARY),
        "accent": (T.ACCENT_SOFT, T.ACCENT),
        "success": (T.SUCCESS_SOFT, T.SUCCESS),
        "warn": (T.WARN_SOFT, T.WARN),
        "danger": (T.DANGER_SOFT, T.DANGER),
    }

    def __init__(self, master, text: str = "", variant: str = "neutral", **kwargs):
        fg, color = self.VARIANTS.get(variant, self.VARIANTS["neutral"])
        super().__init__(
            master,
            text=text,
            font=T.typography.caption_bold(),
            text_color=color,
            fg_color=fg,
            corner_radius=T.R_SM,
            padx=10,
            pady=4,
            **kwargs,
        )
        self._variant = variant

    def set_variant(self, variant: str, text: Optional[str] = None) -> None:
        fg, color = self.VARIANTS.get(variant, self.VARIANTS["neutral"])
        cfg = {"fg_color": fg, "text_color": color}
        if text is not None:
            cfg["text"] = text
        self.configure(**cfg)
        self._variant = variant


# ---------- Поля ввода ----------

class FieldRow(ctk.CTkFrame):
    """Поле с подписью сверху и опциональной справкой снизу."""

    def __init__(
        self,
        master,
        label: str,
        placeholder: str = "",
        hint: str = "",
        show: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=label,
            font=T.typography.caption_bold(),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            height=40,
            corner_radius=T.R_MD,
            border_width=1,
            border_color=T.BORDER,
            fg_color=T.BG_FIELD,
            text_color=T.TEXT_PRIMARY,
            font=T.typography.body(),
            show=show or "",
        )
        self.entry.grid(row=1, column=0, sticky="ew")

        if hint:
            ctk.CTkLabel(
                self,
                text=hint,
                font=T.typography.small(),
                text_color=T.TEXT_TERTIARY,
                anchor="w",
                justify="left",
                wraplength=520,
            ).grid(row=2, column=0, sticky="ew", pady=(6, 0))

    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, value: str) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, value)


# ---------- Кнопки ----------

class PrimaryButton(ctk.CTkButton):
    def __init__(self, master, text: str, command: Optional[Callable] = None, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            height=42,
            corner_radius=T.R_MD,
            font=T.typography.body_bold(),
            fg_color=T.ACCENT,
            hover_color=T.ACCENT_HOVER,
            text_color=T.TEXT_ON_ACCENT,
            **kwargs,
        )


class SecondaryButton(ctk.CTkButton):
    def __init__(self, master, text: str, command: Optional[Callable] = None, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            height=42,
            corner_radius=T.R_MD,
            font=T.typography.body_bold(),
            fg_color="transparent",
            hover_color=T.BG_CARD_INSET,
            text_color=T.TEXT_PRIMARY,
            border_width=1,
            border_color=T.BORDER_STRONG,
            **kwargs,
        )


class DangerButton(ctk.CTkButton):
    def __init__(self, master, text: str, command: Optional[Callable] = None, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            height=42,
            corner_radius=T.R_MD,
            font=T.typography.body_bold(),
            fg_color=T.DANGER,
            hover_color=("#B23128", "#D63A30"),
            text_color="#FFFFFF",
            **kwargs,
        )


class GhostButton(ctk.CTkButton):
    """Бесшовная текстовая кнопка."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            height=36,
            corner_radius=T.R_SM,
            font=T.typography.caption_bold(),
            fg_color="transparent",
            hover_color=T.BG_CARD_INSET,
            text_color=T.ACCENT,
            **kwargs,
        )


# ---------- Степпер ----------

class Stepper(ctk.CTkFrame):
    """Вертикальный нумерованный список шагов в сайдбаре.

    on_jump(index) — необязательный коллбэк навигации (например, для разрешённого
    переключения между уже пройденными шагами).
    """

    def __init__(
        self,
        master,
        steps: list[tuple[str, str]],
        on_jump: Optional[Callable[[int], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._steps = steps
        self._on_jump = on_jump
        self._items: list[dict] = []
        self._current = 0
        self._max_completed = -1

        self.grid_columnconfigure(0, weight=1)
        for i, (title, subtitle) in enumerate(steps):
            self._build_step(i, title, subtitle)
        self.set_current(0)

    def _build_step(self, i: int, title: str, subtitle: str) -> None:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=i, column=0, sticky="ew", pady=(0, T.SP_2))
        row.grid_columnconfigure(1, weight=1)

        bullet = ctk.CTkLabel(
            row,
            text=str(i + 1),
            width=30,
            height=30,
            corner_radius=15,
            fg_color=T.BG_CARD_INSET,
            text_color=T.TEXT_SECONDARY,
            font=T.typography.caption_bold(),
        )
        bullet.grid(row=0, column=0, padx=(0, T.SP_3), pady=4)

        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="ew")
        title_lbl = ctk.CTkLabel(
            text_frame,
            text=title,
            font=T.typography.body_bold(),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        )
        title_lbl.pack(fill="x")
        sub_lbl = ctk.CTkLabel(
            text_frame,
            text=subtitle,
            font=T.typography.small(),
            text_color=T.TEXT_TERTIARY,
            anchor="w",
        )
        sub_lbl.pack(fill="x")

        if self._on_jump is not None:
            def go(_e=None, idx=i):
                if idx <= self._max_completed + 1:
                    self._on_jump(idx)

            for widget in (row, bullet, text_frame, title_lbl, sub_lbl):
                widget.bind("<Button-1>", go)
                widget.configure(cursor="hand2")

        self._items.append({
            "row": row,
            "bullet": bullet,
            "title": title_lbl,
            "subtitle": sub_lbl,
        })

    def set_current(self, index: int) -> None:
        self._current = index
        self._max_completed = max(self._max_completed, index - 1)
        for i, it in enumerate(self._items):
            if i < index:
                # завершённый шаг — зелёная галочка
                it["bullet"].configure(
                    text="✓",
                    fg_color=T.SUCCESS,
                    text_color="#FFFFFF",
                )
                it["title"].configure(text_color=T.TEXT_SECONDARY)
                it["subtitle"].configure(text_color=T.TEXT_TERTIARY)
            elif i == index:
                it["bullet"].configure(
                    text=str(i + 1),
                    fg_color=T.ACCENT,
                    text_color="#FFFFFF",
                )
                it["title"].configure(text_color=T.TEXT_PRIMARY)
                it["subtitle"].configure(text_color=T.TEXT_SECONDARY)
            else:
                it["bullet"].configure(
                    text=str(i + 1),
                    fg_color=T.BG_CARD_INSET,
                    text_color=T.TEXT_TERTIARY,
                )
                it["title"].configure(text_color=T.TEXT_SECONDARY)
                it["subtitle"].configure(text_color=T.TEXT_TERTIARY)


# ---------- Подвал с навигацией ----------

class FooterBar(ctk.CTkFrame):
    """Полоса действий внизу экрана с разделителем сверху."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(1, weight=1)

        self._divider = ctk.CTkFrame(self, height=1, fg_color=T.BORDER, corner_radius=0)
        self._divider.grid(row=0, column=0, columnspan=3, sticky="ew")

        self.left = ctk.CTkFrame(self, fg_color="transparent")
        self.left.grid(row=1, column=0, sticky="w", pady=(T.SP_4, 0))

        self.center = ctk.CTkFrame(self, fg_color="transparent")
        self.center.grid(row=1, column=1, sticky="ew", pady=(T.SP_4, 0))

        self.right = ctk.CTkFrame(self, fg_color="transparent")
        self.right.grid(row=1, column=2, sticky="e", pady=(T.SP_4, 0))

"""Дизайн-система: цвета, типографика, размеры.

Палитра вдохновлена Apple HIG (системными цветами macOS / iOS): мягкий
нейтральный фон, плотные карточки, контрастный акцент. Все цвета объявлены
парами (light, dark), что позволяет CustomTkinter автоматически подбирать
вариант под текущую тему оформления.
"""

from __future__ import annotations

import tkinter.font as tkfont
from dataclasses import dataclass


# ---------- Цветовая палитра ----------

# Парные значения: (light, dark)

# Фон страницы
BG_PAGE = ("#F5F5F7", "#1A1A1C")

# Сайдбар (немного отличается от фона страницы)
BG_SIDEBAR = ("#FFFFFF", "#1F1F22")

# Карточки и поверхности
BG_CARD = ("#FFFFFF", "#26262A")
BG_CARD_INSET = ("#F2F2F5", "#2C2C30")   # вложенные блоки, лог, таблицы
BG_FIELD = ("#F2F2F5", "#2C2C30")

# Разделители / границы
BORDER = ("#E4E4E8", "#3A3A3F")
BORDER_STRONG = ("#D2D2D7", "#48484C")

# Текст
TEXT_PRIMARY = ("#1D1D1F", "#F5F5F7")
TEXT_SECONDARY = ("#6E6E73", "#9A9AA1")
TEXT_TERTIARY = ("#8E8E93", "#7A7A80")
TEXT_ON_ACCENT = ("#FFFFFF", "#FFFFFF")

# Акцент (системный синий)
ACCENT = ("#0A84FF", "#0A84FF")
ACCENT_HOVER = ("#0066CC", "#3D9BFF")
ACCENT_SOFT = ("#E5F0FF", "#0E2A47")     # фон pill, мягкий бэйдж

# Семантические
SUCCESS = ("#30B650", "#34C759")
SUCCESS_SOFT = ("#E3F7E8", "#143D1F")
WARN = ("#F0A020", "#FFB340")
WARN_SOFT = ("#FFF3D6", "#3D2A0A")
DANGER = ("#E0392B", "#FF453A")
DANGER_SOFT = ("#FBE3E1", "#3D1614")

# ---------- Радиусы ----------

R_LG = 18    # большие карточки
R_MD = 12    # поля, кнопки
R_SM = 8     # пилюли, мелкие элементы
R_XS = 6


# ---------- Отступы ----------

SP_1 = 4
SP_2 = 8
SP_3 = 12
SP_4 = 16
SP_5 = 24
SP_6 = 32
SP_7 = 48


# ---------- Типографика ----------

_FONT_FAMILY_CANDIDATES = (
    "SF Pro Display",
    "SF Pro Text",
    "-apple-system",
    "Inter",
    "Segoe UI Variable",
    "Segoe UI",
    "Helvetica Neue",
    "Helvetica",
    "Arial",
)

_FONT_MONO_CANDIDATES = (
    "JetBrains Mono",
    "SF Mono",
    "Menlo",
    "Consolas",
    "DejaVu Sans Mono",
    "Courier New",
    "Courier",
)


@dataclass(frozen=True)
class FontSpec:
    family: str
    size: int
    weight: str = "normal"

    def as_tuple(self) -> tuple:
        return (self.family, self.size, self.weight) if self.weight != "normal" else (self.family, self.size)


class _Typography:
    """Лениво инициализируемая типографика — после создания Tk root."""

    def __init__(self) -> None:
        self._family: str | None = None
        self._mono: str | None = None

    def _pick(self, candidates: tuple[str, ...], default: str) -> str:
        try:
            available = set(tkfont.families())
        except Exception:
            return default
        for c in candidates:
            if c in available:
                return c
        return default

    @property
    def family(self) -> str:
        if self._family is None:
            self._family = self._pick(_FONT_FAMILY_CANDIDATES, "TkDefaultFont")
        return self._family

    @property
    def mono(self) -> str:
        if self._mono is None:
            self._mono = self._pick(_FONT_MONO_CANDIDATES, "TkFixedFont")
        return self._mono

    # Иерархия размеров (схожа с macOS Sonoma)
    def display(self) -> tuple:
        return (self.family, 32, "bold")

    def title(self) -> tuple:
        return (self.family, 24, "bold")

    def section(self) -> tuple:
        return (self.family, 17, "bold")

    def body_bold(self) -> tuple:
        return (self.family, 14, "bold")

    def body(self) -> tuple:
        return (self.family, 14)

    def caption(self) -> tuple:
        return (self.family, 12)

    def caption_bold(self) -> tuple:
        return (self.family, 12, "bold")

    def small(self) -> tuple:
        return (self.family, 11)

    def code(self) -> tuple:
        return (self.mono, 12)


typography = _Typography()

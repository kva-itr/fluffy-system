"""Точка входа приложения MAX Group Inviter.

    pip install -r requirements.txt
    python app.py
"""

from ui.window import App


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()

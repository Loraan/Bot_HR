"""Точка входа в приложение бота."""

from app import bot, state
from storage.db import init_db
from storage.progress import load_progress

# Импорт регистрирует все хендлеры на боте
import handlers  # noqa: F401


def main() -> None:
    print("Бот запущен...")
    init_db()          # создание таблиц, если их ещё нет
    load_progress(state)
    bot.infinity_polling()


if __name__ == "__main__":
    main()

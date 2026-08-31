"""Проверка прав и авторизации пользователей."""

from functools import wraps

import config
from storage import users as storage_users


def is_admin(user_id: int) -> bool:
    """Проверяет, обладает ли пользователь правами администратора."""
    return user_id in config.ADMIN_IDS


def get_role(user_id: int) -> str:
    """Возвращает роль пользователя: 'Admin' или 'User'."""
    return "Admin" if is_admin(user_id) else "User"


def is_registered(user_id: int) -> bool:
    """Проверяет, зарегистрирован ли пользователь (авторизован)."""
    return storage_users.user_exists(user_id)


def require_registration(handler):
    """Декоратор: пропускает только авторизованных пользователей.

    Если пользователь не зарегистрирован — просит сначала пройти /start
    и не выполняет логику обработчика.
    """
    from app import bot

    @wraps(handler)
    def wrapper(message_or_call):
        user_id = message_or_call.from_user.id
        if not is_registered(user_id):
            # Определяем, с чем работаем: callback или обычное сообщение
            if hasattr(message_or_call, "message"):
                bot.answer_callback_query(message_or_call.id)
                chat_id = message_or_call.message.chat.id
            else:
                chat_id = message_or_call.chat.id

            bot.send_message(chat_id, "⚠️ Сначала зарегистрируйтесь через /start.")
            return

        return handler(message_or_call)

    return wrapper

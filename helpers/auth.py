"""Проверка прав пользователей."""

import config


def is_admin(user_id: int) -> bool:
    """Проверяет, обладает ли пользователь правами администратора."""
    return user_id in config.ADMIN_IDS


def get_role(user_id: int) -> str:
    """Возвращает роль пользователя: 'Admin' или 'User'."""
    return "Admin" if is_admin(user_id) else "User"

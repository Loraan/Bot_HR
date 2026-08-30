"""Работа с таблицей пользователей (SQLite, таблица users).

Бывший UserTable.txt: id | Имя | Фамилия
"""

import config
from storage import db


def user_exists(user_id: int) -> bool:
    """Проверяет, есть ли уже такой user_id в таблице users."""
    conn = db.get_connection()
    try:
        row = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row is not None
    finally:
        conn.close()


def save_user(user_id: int, first_name: str, last_name: str) -> None:
    """Записывает нового пользователя в таблицу users."""
    conn = db.get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id, first_name, last_name) VALUES (?, ?, ?)",
                (user_id, first_name, last_name),
            )
    finally:
        conn.close()


def load_users() -> dict:
    """Загружает всех пользователей. Возвращает {user_id: (имя, фамилия)}."""
    conn = db.get_connection()
    try:
        rows = conn.execute("SELECT user_id, first_name, last_name FROM users").fetchall()
        return {row["user_id"]: (row["first_name"], row["last_name"]) for row in rows}
    finally:
        conn.close()


def load_user_lines() -> list:
    """Возвращает список строк вида 'id | Имя | Фамилия' (для /users)."""
    conn = db.get_connection()
    try:
        rows = conn.execute("SELECT user_id, first_name, last_name FROM users").fetchall()
        return [
            f"{row['user_id']} | {row['first_name']} | {row['last_name']}"
            for row in rows
        ]
    finally:
        conn.close()
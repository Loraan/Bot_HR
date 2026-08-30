"""Работа с обратной связью (SQLite, таблица feedback).

Бывший FeedBack.txt: id | Имя | Фамилия | текст обратной связи
"""

from storage import db


def save_feedback(user_id: int, first_name: str, last_name: str, feedback: str) -> None:
    """Записывает обратную связь в таблицу feedback."""
    conn = db.get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO feedback (user_id, first_name, last_name, feedback) VALUES (?, ?, ?, ?)",
                (user_id, first_name, last_name, feedback),
            )
    finally:
        conn.close()


def load_feedback() -> list:
    """Загружает все записи обратной связи.

    Возвращает список кортежей (user_id, first_name, last_name, feedback).
    """
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT user_id, first_name, last_name, feedback FROM feedback ORDER BY id"
        ).fetchall()
        return [
            (row["user_id"], row["first_name"], row["last_name"], row["feedback"])
            for row in rows
        ]
    finally:
        conn.close()
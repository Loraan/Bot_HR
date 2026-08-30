"""Работа с маршрутами (SQLite, таблица routes).

Бывший Routes.txt: Название | Описание
"""

from storage import db


def load_routes() -> list:
    """Загружает все маршруты. Возвращает список пар (название, описание)."""
    conn = db.get_connection()
    try:
        rows = conn.execute("SELECT name, description FROM routes ORDER BY id").fetchall()
        return [(row["name"], row["description"]) for row in rows]
    finally:
        conn.close()


def save_route(name: str, description: str) -> None:
    """Добавляет новый маршрут в таблицу routes."""
    conn = db.get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO routes (name, description) VALUES (?, ?)",
                (name, description),
            )
    finally:
        conn.close()
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


def get_route_id(index: int):
    """Возвращает id маршрута по его индексу (0-based) в списке, либо None."""
    conn = db.get_connection()
    try:
        row = conn.execute("SELECT id FROM routes ORDER BY id LIMIT 1 OFFSET ?", (index,)).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def save_route(name: str, description: str) -> int:
    """Добавляет новый маршрут в таблицу routes. Возвращает id нового маршрута."""
    conn = db.get_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO routes (name, description) VALUES (?, ?)",
                (name, description),
            )
        return cur.lastrowid
    finally:
        conn.close()


def delete_route(route_id: int) -> None:
    """Удаляет маршрут по id."""
    conn = db.get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM routes WHERE id = ?", (route_id,))
    finally:
        conn.close()
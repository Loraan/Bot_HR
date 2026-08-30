"""Сохранение и получение фотографий, подтверждающих выполнение заданий.

Картинки сохраняются в отдельную папку (config.PHOTOS_DIR),
а в таблице photos хранится путь к файлу.

Имя файла: user_{user_id}_route_{route_index}_task_{task_index}_{timestamp}.jpg
"""

import os
import time
import uuid

import config
from storage import db


def load_photos_by_task(user_id: int, route_index: int, task_index: int) -> list:
    """Возвращает список путей к фото пользователя для конкретной активности."""
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT file_path FROM photos "
            "WHERE user_id = ? AND route_index = ? AND task_index = ? "
            "ORDER BY id",
            (user_id, route_index, task_index),
        ).fetchall()
        return [row["file_path"] for row in rows]
    finally:
        conn.close()


def save_photo(user_id: int, route_index: int, task_index: int, file_bytes: bytes) -> str:
    """Сохраняет фото на диск и записывает путь в таблицу photos.

    Возвращает путь к сохранённому файлу.
    """
    # Гарантируем существование папки для фото
    os.makedirs(config.PHOTOS_DIR, exist_ok=True)

    # Уникальное имя файла (добавляем timestamp и короткий uuid во избежание коллизий)
    timestamp = int(time.time())
    unique = uuid.uuid4().hex[:8]
    filename = f"user_{user_id}_route_{route_index}_task_{task_index}_{timestamp}_{unique}.jpg"
    file_path = os.path.join(config.PHOTOS_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    conn = db.get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO photos (user_id, route_index, task_index, file_path) "
                "VALUES (?, ?, ?, ?)",
                (user_id, route_index, task_index, file_path),
            )
    finally:
        conn.close()

    return file_path
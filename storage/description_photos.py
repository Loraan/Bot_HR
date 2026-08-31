"""Сохранение и получение фотографий для описания маршрута.

Картинки сохраняются в отдельную папку (config.DESCRIPTION_PHOTOS_DIR),
а в таблице description_photos хранится путь к файлу, привязанный к маршруту.

Имя файла: route_{route_id}_{timestamp}_{uuid}.jpg
"""

import os
import time
import uuid

import config
from storage import db


def load_photos_by_route(route_id: int) -> list:
    """Возвращает список путей к фото описания для конкретного маршрута."""
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT file_path FROM description_photos "
            "WHERE route_id = ? "
            "ORDER BY id",
            (route_id,),
        ).fetchall()
        return [row["file_path"] for row in rows]
    finally:
        conn.close()


def delete_photos_by_route(route_id: int) -> None:
    """Удаляет записи о фото описания маршрута и сами файлы с диска."""
    conn = db.get_connection()
    try:
        paths = [
            row["file_path"]
            for row in conn.execute(
                "SELECT file_path FROM description_photos WHERE route_id = ?",
                (route_id,),
            ).fetchall()
        ]
        with conn:
            conn.execute("DELETE FROM description_photos WHERE route_id = ?", (route_id,))
    finally:
        conn.close()

    # Удаляем файлы с диска
    for path in paths:
        try:
            os.remove(path)
        except OSError:
            continue


def save_photo(route_id: int, file_bytes: bytes) -> str:
    """Сохраняет фото на диск и записывает путь в таблицу description_photos.

    Возвращает путь к сохранённому файлу.
    """
    # Гарантируем существование папки для фото
    os.makedirs(config.DESCRIPTION_PHOTOS_DIR, exist_ok=True)

    # Уникальное имя файла (добавляем timestamp и короткий uuid во избежание коллизий)
    timestamp = int(time.time())
    unique = uuid.uuid4().hex[:8]
    filename = f"route_{route_id}_{timestamp}_{unique}.jpg"
    file_path = os.path.join(config.DESCRIPTION_PHOTOS_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    conn = db.get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO description_photos (route_id, file_path) "
                "VALUES (?, ?)",
                (route_id, file_path),
            )
    finally:
        conn.close()

    return file_path
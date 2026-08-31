"""Подключение к базе данных SQLite и создание таблиц.

Используются те же названия и параметры, что были в txt-файлах:
- users     (бывший UserTable.txt): id | Имя | Фамилия
- routes    (бывший Routes.txt):     Название | Описание
- progress  (бывший Progress.txt):   user_id | Название:Действия;...
- feedback  (бывший FeedBack.txt):   id | Имя | Фамилия | текст

Защита от блокировок при работе нескольких пользователей:
- check_same_thread=False — разрешает обращение к соединению из разных потоков
- journal_mode=WAL       — позволяет параллельные чтения во время записи
- busy_timeout=5000      — ждёт до 5 секунд, если база занята, вместо мгновенной ошибки
- row_factory            — доступ к колонкам по имени
"""

import os
import sqlite3
import threading

import config

# Блокировка для последовательного доступа к БД (дополнительная защита записи)
_lock = threading.Lock()


def get_connection() -> sqlite3.Connection:
    """Создаёт и настраивает соединение с базой данных."""
    # Гарантируем, что директория с базой существует
    os.makedirs(os.path.dirname(config.DATABASE_FILE), exist_ok=True)

    conn = sqlite3.connect(config.DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def init_db() -> None:
    """Создаёт все таблицы, если их ещё нет."""
    with _lock:
        conn = get_connection()
        try:
            with conn:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        user_id    INTEGER PRIMARY KEY,
                        first_name TEXT NOT NULL,
                        last_name  TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS routes (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        name        TEXT NOT NULL,
                        description TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS progress (
                        user_id        INTEGER NOT NULL,
                        route_index    INTEGER NOT NULL,
                        done_tasks     TEXT NOT NULL DEFAULT '',
                        is_completed   INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (user_id, route_index)
                    );

                    CREATE TABLE IF NOT EXISTS feedback (
                        id         INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id    INTEGER NOT NULL,
                        first_name TEXT NOT NULL,
                        last_name  TEXT NOT NULL,
                        feedback   TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS photos (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id     INTEGER NOT NULL,
                        route_index INTEGER NOT NULL,
                        task_index  INTEGER NOT NULL,
                        file_path   TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS description_photos (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        route_id    INTEGER NOT NULL,
                        file_path   TEXT NOT NULL
                    );
                    """
                )
        finally:
            conn.close()
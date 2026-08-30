"""Работа с прогрессом выполнения маршрутов (SQLite, таблица progress).

Бывший Progress.txt: user_id | Название_маршрута:Действие1,Действие2;...
В БД хранится как отдельные строки (user_id, route_index, done_tasks, is_completed).
"""

import config
from storage import db
from storage.routes import load_routes

# Сопоставление названий действий и их индексов
_TASK_NAME_TO_INDEX = {task: i for i, task in enumerate(config.ROUTE_TASKS)}
_INDEX_TO_TASK_NAME = {i: task for i, task in enumerate(config.ROUTE_TASKS)}

# Сопоставление названий действий и их индексов
_TASK_NAME_TO_INDEX = {task: i for i, task in enumerate(config.ROUTE_TASKS)}
_INDEX_TO_TASK_NAME = {i: task for i, task in enumerate(config.ROUTE_TASKS)}


def load_progress(state) -> None:
    """Загружает прогресс из таблицы progress в state.progress."""
    state.progress = {}

    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT user_id, route_index, done_tasks, is_completed FROM progress"
        ).fetchall()
    finally:
        conn.close()

    for row in rows:
        user_id = row["user_id"]
        route_index = row["route_index"]
        done_tasks_str = row["done_tasks"]
        is_completed = bool(row["is_completed"])

        user_data = state.progress.setdefault(
            user_id, {"completed_routes": set()}
        )

        done_tasks = set()
        for task_index in done_tasks_str.split(","):
            task_index = task_index.strip()
            if task_index.isdigit():
                done_tasks.add(int(task_index))

        if done_tasks:
            user_data[route_index] = done_tasks

        if is_completed:
            user_data["completed_routes"].add(route_index)


def save_progress(state) -> None:
    """Сохраняет state.progress в таблицу progress (полная перезапись)."""
    conn = db.get_connection()
    try:
        with conn:
            # Полная перезапись: удаляем старые данные и пишем актуальные
            conn.execute("DELETE FROM progress")
            for user_id, data in state.progress.items():
                # Собираем индексы маршрутов с выполненными действиями
                route_indexes = set()
                for key, value in data.items():
                    if key in ("completed_routes", "current_route"):
                        continue
                    if isinstance(value, (set, list, tuple)) and value:
                        route_indexes.add(key)

                # Маршруты из completed_routes
                route_indexes.update(data.get("completed_routes", set()))

                for route_index in route_indexes:
                    done_tasks = data.get(route_index, set())
                    done_tasks_str = ",".join(str(i) for i in sorted(done_tasks))
                    is_completed = route_index in data.get("completed_routes", set())

                    conn.execute(
                        "INSERT INTO progress (user_id, route_index, done_tasks, is_completed) "
                        "VALUES (?, ?, ?, ?)",
                        (user_id, route_index, done_tasks_str, int(is_completed)),
                    )
    finally:
        conn.close()


def users_with_progress() -> list:
    """Возвращает список user_id, у которых выполнена хотя бы одна активность.

    Берём пользователей, у которых в таблице progress есть непустой done_tasks
    (выполнен хотя бы один пункт маршрута).
    """
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT user_id FROM progress WHERE done_tasks != ''"
        ).fetchall()
        return [row["user_id"] for row in rows]
    finally:
        conn.close()


def routes_with_progress(user_id: int) -> list:
    """Возвращает список индексов маршрутов пользователя, где выполнена хотя бы одна активность."""
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT route_index FROM progress WHERE user_id = ? AND done_tasks != ''",
            (user_id,),
        ).fetchall()
        return [row["route_index"] for row in rows]
    finally:
        conn.close()


def tasks_done(user_id: int, route_index: int) -> list:
    """Возвращает отсортированный список индексов выполненных активностей пользователя в маршруте."""
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT done_tasks FROM progress WHERE user_id = ? AND route_index = ?",
            (user_id, route_index),
        ).fetchone()
        if row is None or not row["done_tasks"]:
            return []
        return sorted(int(i) for i in row["done_tasks"].split(",") if i.isdigit())
    finally:
        conn.close()
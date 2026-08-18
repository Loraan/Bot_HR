"""Подсчёт баллов пользователя на основе выполненных действий."""

import config


def count_done_tasks(user_data: dict) -> int:
    """Возвращает общее число выполненных действий пользователя.

    user_data — значение из state.progress для конкретного user_id:
        {index_маршрута: set(индексов_действий), "completed_routes": set, ...}
    """
    total = 0
    for key, value in user_data.items():
        if key in ("completed_routes", "current_route"):
            continue
        if isinstance(value, (set, list, tuple)):
            total += len(value)
    return total


def user_score(user_data: dict) -> int:
    """Возвращает число баллов пользователя (5 за каждое выполненное действие)."""
    return count_done_tasks(user_data) * config.POINTS_PER_TASK

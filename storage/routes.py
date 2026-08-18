"""Работа с маршрутами (Routes.txt).

Формат строки: Название | Описание
"""

import config


def load_routes() -> list:
    """Загружает все маршруты из файла. Возвращает список пар (название, описание)."""
    try:
        with open(config.ROUTES_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

    routes_list = []
    for line in lines:
        parts = line.split(" | ", 1)
        name = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else "Без описания"
        routes_list.append((name, description))
    return routes_list


def save_route(name: str, description: str) -> None:
    """Добавляет новый маршрут в файл в формате: Название | Описание."""
    with open(config.ROUTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"{name} | {description}\n")

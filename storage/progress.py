"""Работа с прогрессом выполнения маршрутов (Progress.txt).

Формат строки: user_id | Название_маршрута:Действие1,Действие2;Название2:Действие1;...
"""

import os

import config
from storage.routes import load_routes


def load_progress(state) -> None:
    """Загружает прогресс из файла Progress.txt в state.progress."""
    state.progress = {}

    # Сопоставление названий маршрутов и их индексов
    name_to_index = {name: i for i, (name, _) in enumerate(load_routes())}
    # Сопоставление названий действий и их индексов
    task_name_to_index = {task: i for i, task in enumerate(config.ROUTE_TASKS)}

    try:
        with open(config.PROGRESS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or " | " not in line:
                    continue
                user_part, routes_part = line.split(" | ", 1)
                try:
                    user_id = int(user_part.strip())
                except ValueError:
                    continue

                user_data = {"completed_routes": set()}

                for route_part in routes_part.split(";"):
                    route_part = route_part.strip()
                    if not route_part:
                        continue

                    # Разделяем название маршрута и выполненные действия
                    if ":" in route_part:
                        route_name, tasks_part = route_part.split(":", 1)
                    else:
                        # Старый формат без действий
                        route_name, tasks_part = route_part, ""

                    route_name = route_name.strip()
                    if route_name not in name_to_index:
                        continue

                    route_index = name_to_index[route_name]

                    # Восстанавливаем выполненные действия
                    done_tasks = set()
                    for task_name in tasks_part.split(","):
                        task_name = task_name.strip()
                        if task_name and task_name in task_name_to_index:
                            done_tasks.add(task_name_to_index[task_name])

                    if done_tasks:
                        user_data[route_index] = done_tasks
                        # Маршрут считается выполненным, только если выполнены ВСЕ действия
                        if len(done_tasks) == len(config.ROUTE_TASKS):
                            user_data["completed_routes"].add(route_index)
                    else:
                        # Старый формат без списка действий - считаем маршрут завершённым
                        user_data["completed_routes"].add(route_index)

                state.progress[user_id] = user_data
    except FileNotFoundError:
        return


def save_progress(state) -> None:
    """Сохраняет state.progress в файл Progress.txt."""
    os.makedirs(os.path.dirname(config.PROGRESS_FILE), exist_ok=True)

    routes_list = load_routes()
    # Сопоставление индексов маршрутов и их названий
    index_to_name = {i: name for i, (name, _) in enumerate(routes_list)}
    # Сопоставление индексов действий и их названий
    index_to_task_name = {i: task for i, task in enumerate(config.ROUTE_TASKS)}

    with open(config.PROGRESS_FILE, "w", encoding="utf-8") as f:
        for user_id, data in state.progress.items():
            # Собираем индексы маршрутов, где есть выполненные действия,
            # либо которые добавлены в completed_routes
            route_indexes = set()
            for key, value in data.items():
                if key in ("completed_routes", "current_route"):
                    continue
                if isinstance(value, (set, list, tuple)) and value:
                    route_indexes.add(key)
            route_indexes.update(data.get("completed_routes", set()))

            if not route_indexes:
                continue

            # Собираем части: "Название маршрута:Действие1,Действие2"
            route_parts = []
            for route_index in route_indexes:
                if route_index not in index_to_name:
                    continue

                route_name = index_to_name[route_index]
                done_tasks = data.get(route_index, set())

                if done_tasks:
                    task_names = [
                        index_to_task_name[i]
                        for i in done_tasks
                        if i in index_to_task_name
                    ]
                    route_parts.append(f"{route_name}:{','.join(task_names)}")
                else:
                    route_parts.append(route_name)

            if route_parts:
                f.write(f"{user_id} | {';'.join(route_parts)}\n")

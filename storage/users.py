"""Работа с таблицей пользователей (UserTable.txt).

Формат строки: id | Имя | Фамилия
"""

import config


def user_exists(user_id: int) -> bool:
    """Проверяет, есть ли уже такой user_id в файле UserTable."""
    try:
        with open(config.USER_TABLE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(" | ")
                # Формат строки: id | Имя | Фамилия
                if parts and parts[0] == str(user_id):
                    return True
    except FileNotFoundError:
        # Файла ещё нет — значит пользователей точно нет
        return False
    return False


def save_user(user_id: int, first_name: str, last_name: str) -> None:
    """Записывает нового пользователя в файл UserTable."""
    with open(config.USER_TABLE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{user_id} | {first_name} | {last_name}\n")


def load_users() -> dict:
    """Загружает всех пользователей. Возвращает {user_id: (имя, фамилия)}."""
    users = {}
    try:
        with open(config.USER_TABLE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(" | ")
                if len(parts) == 3:
                    try:
                        user_id = int(parts[0].strip())
                    except ValueError:
                        continue
                    users[user_id] = (parts[1].strip(), parts[2].strip())
    except FileNotFoundError:
        pass
    return users


def load_user_lines() -> list:
    """Возвращает список непустых строк файла UserTable."""
    try:
        with open(config.USER_TABLE_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

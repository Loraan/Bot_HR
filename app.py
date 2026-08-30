"""Единая точка создания бота и хранения общих состояний приложения."""

import os
import sys

import telebot

# Токен бота берётся из переменной окружения BOT_TOKEN.
# Если переменная не задана — запрашиваем его при запуске вручную.
# Это позволяет не хранить токен в самом проекте.
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    TOKEN = input("Введите токен бота от @BotFather: ").strip()
    if not TOKEN:
        print("Ошибка: токен не может быть пустым. Задайте переменную окружения BOT_TOKEN.")
        sys.exit(1)

# Единственный экземпляр бота, используемый во всех хендлерах
bot = telebot.TeleBot(TOKEN)


class AppState:
    """Глобальные состояния бота, общие для разных хендлеров."""

    def __init__(self):
        # Прогресс выполнения маршрутов:
        # {user_id: {index_маршрута: set(выполненных_пунктов), "completed_routes": set, "current_route": int}}
        self.progress = {}

        # Промежуточные данные регистрации: {chat_id: {...}}
        self.registration_data = {}

        # Данные добавления маршрута: {chat_id: {...}}
        self.route_data = {}

        # Ожидание фотографии: {chat_id: (индекс_маршрута, индекс_пункта)}
        self.photo_upload = {}


# Общее состояние всего приложения
state = AppState()
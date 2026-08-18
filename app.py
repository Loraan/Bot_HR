"""Единая точка создания бота и хранения общих состояний приложения."""

import telebot

import config

# Единственный экземпляр бота, используемый во всех хендлерах
bot = telebot.TeleBot(config.TOKEN)


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

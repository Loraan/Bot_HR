"""Хендлеры администрирования: добавление маршрута (только для админов)."""

from telebot import types

from app import bot, state
from helpers.auth import is_admin
from helpers.keyboards import main_menu_keyboard
from storage import routes as storage_routes


@bot.message_handler(func=lambda m: m.text == "➕ Добавить маршрут")
def add_route(message):
    """Добавление нового маршрута (только для администраторов)."""
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ У вас недостаточно прав для этой операции.")
        return

    state.route_data[message.chat.id] = {}
    bot.send_message(
        message.chat.id,
        "Введите название нового маршрута:",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(message, get_route_name)


def get_route_name(message):
    """Получает название маршрута и запрашивает описание."""
    if message.text is None:
        bot.send_message(message.chat.id, "Пожалуйста, введите название маршрута текстом:")
        bot.register_next_step_handler(message, get_route_name)
        return

    state.route_data[message.chat.id]["name"] = message.text.strip()
    bot.send_message(message.chat.id, "Введите описание маршрута:")
    bot.register_next_step_handler(message, get_route_description)


def get_route_description(message):
    """Получает описание маршрута и сохраняет его в файл."""
    if message.text is None:
        bot.send_message(message.chat.id, "Пожалуйста, введите описание маршрута текстом:")
        bot.register_next_step_handler(message, get_route_description)
        return

    route_name = state.route_data[message.chat.id]["name"]
    route_desc = message.text.strip()

    # Сохраняем маршрут в файл в формате: Название | Описание
    storage_routes.save_route(route_name, route_desc)

    state.route_data.pop(message.chat.id, None)

    bot.send_message(
        message.chat.id,
        f"✅ Маршрут \"{route_name}\" добавлен!",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )

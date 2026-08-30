"""Построение клавиатур."""

from telebot import types

import config
from helpers.auth import is_admin


def main_menu_keyboard(user_id: int) -> types.ReplyKeyboardMarkup:
    """Клавиатура главного меню.
    Кнопка "Обратная связь" показывается только обычным пользователям,
    а для админов — кнопка "Админка"."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(config.BTN_RATING)
    keyboard.row(config.BTN_ROUTES)
    if is_admin(user_id):
        keyboard.row(config.BTN_ADMIN)
    else:
        keyboard.row(config.BTN_FEEDBACK)
    return keyboard


def admin_menu_keyboard() -> types.ReplyKeyboardMarkup:
    """Клавиатура админ-меню с кнопками управления."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(config.BTN_ADD_ROUTE)
    keyboard.row(config.BTN_VIEW_FEEDBACK)
    keyboard.row(config.BTN_VIEW_PHOTOS)
    keyboard.row(config.BTN_BACK)
    return keyboard


def cancel_keyboard() -> types.ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(config.BTN_CANCEL)
    return keyboard


def routes_keyboard(routes_list: list, completed: set) -> types.InlineKeyboardMarkup:
    """Клавиатура со списком маршрутов. Выполненные помечаются галочкой."""
    keyboard = types.InlineKeyboardMarkup()
    for i, (name, _desc) in enumerate(routes_list):
        label = ("✅ " if i in completed else "") + name
        keyboard.add(types.InlineKeyboardButton(label, callback_data=f"route:{i}"))
    return keyboard


def route_detail_keyboard(route_index: int) -> types.InlineKeyboardMarkup:
    """Клавиатура деталей маршрута: Назад и Выполнить."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("⬅️ Назад", callback_data="routes_back"),
        types.InlineKeyboardButton("✅ Выполнить", callback_data=f"do_route:{route_index}"),
    )
    return keyboard

"""Хендлеры администрирования: добавление маршрута (только для админов)."""

from telebot import types

from app import bot, state
from helpers.auth import is_admin, require_registration
from helpers.keyboards import admin_menu_keyboard
from storage import description_photos as storage_description_photos
from storage import routes as storage_routes
import config


@bot.message_handler(func=lambda m: m.text == "➕ Добавить маршрут")
@require_registration
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


@bot.message_handler(commands=["cancel"])
def cancel_route(message):
    """Отмена создания маршрута (доступна на любом этапе)."""
    if message.chat.id not in state.route_data:
        bot.send_message(
            message.chat.id,
            "Сейчас нет активного процесса создания маршрута.",
            reply_markup=admin_menu_keyboard(),
        )
        return
    _abort_route(message.chat.id)


@bot.message_handler(commands=["done"])
@require_registration
def done_route(message):
    """Завершает добавление фотографий к описанию маршрута."""
    if message.chat.id not in state.route_data:
        return
    _finish_route(message.chat.id)


def _is_cancel(message) -> bool:
    """Проверяет, является ли сообщение командой отмены или кнопкой 'Отмена'."""
    return message.text in (config.BTN_CANCEL, "/cancel")


def _abort_route(chat_id):
    """Прерывает создание маршрута и очищает временные данные.

    Если маршрут уже был сохранён в БД, он удаляется вместе с фотографиями.
    """
    data = state.route_data.pop(chat_id, None) or {}

    route_id = data.get("route_id")
    if route_id is not None:
        storage_description_photos.delete_photos_by_route(route_id)
        storage_routes.delete_route(route_id)

    bot.send_message(
        chat_id,
        "🚫 Создание маршрута отменено.",
        reply_markup=admin_menu_keyboard(),
    )


def _save_desc_photo(route_id: int, message) -> int:
    """Сохраняет фотографию из сообщения и возвращает количество фото маршрута."""
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    file_bytes = bot.download_file(file_info.file_path)
    storage_description_photos.save_photo(route_id, file_bytes)
    return len(storage_description_photos.load_photos_by_route(route_id))


def _ask_more_photos(chat_id):
    """Просит добавить ещё фото либо завершить через /done."""
    bot.send_message(
        chat_id,
        "📷 Если нужно, прикрепите ещё фотографии к описанию (по одной)\n"
        "или нажмите /done для завершения:",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row(config.BTN_CANCEL),
    )


def get_route_name(message):
    """Получает название маршрута и запрашивает описание."""
    if _is_cancel(message):
        _abort_route(message.chat.id)
        return

    if message.text is None:
        bot.send_message(
            message.chat.id,
            "Пожалуйста, введите название маршрута текстом:",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row(config.BTN_CANCEL),
        )
        bot.register_next_step_handler(message, get_route_name)
        return

    state.route_data[message.chat.id]["name"] = message.text.strip()
    bot.send_message(
        message.chat.id,
        "Отправьте описание маршрута.\n"
        "Можно просто текстом, а можно прикрепить фотографию (или несколько) — "
        "тогда текст подписи к фото станет описанием маршрута и "
        "будет показываться вместе с фотографиями:",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row(config.BTN_CANCEL),
    )
    bot.register_next_step_handler(message, get_route_description)


def get_route_description(message):
    """Получает описание (и, при наличии, первое фото) и сохраняет маршрут."""
    if _is_cancel(message):
        _abort_route(message.chat.id)
        return

    route_name = state.route_data[message.chat.id]["name"]

    # Описание может быть в подписи к фото (html_caption) или в текстовом сообщении (html_text)
    if message.photo:
        route_desc = (message.html_caption or message.caption or "").strip()
        if not route_desc:
            bot.send_message(
                message.chat.id,
                "Фотография должна быть с подписью-описанием. "
                "Отправьте описание маршрута ещё раз (текстом или фото с подписью):",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row(config.BTN_CANCEL),
            )
            bot.register_next_step_handler(message, get_route_description)
            return
    else:
        if message.text is None:
            bot.send_message(
                message.chat.id,
                "Пожалуйста, отправьте описание маршрута (текстом или фото с подписью):",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row(config.BTN_CANCEL),
            )
            bot.register_next_step_handler(message, get_route_description)
            return
        route_desc = (message.html_text or message.text).strip()

    # Сохраняем маршрут
    route_id = storage_routes.save_route(route_name, route_desc)
    state.route_data[message.chat.id]["route_id"] = route_id

    # Если к описанию прикреплено фото — сохраняем его
    if message.photo:
        _save_desc_photo(route_id, message)

    # Переходим в режим сбора дополнительных фотографий (по одной).
    # Этот режим обрабатывает и альбомы: каждое фото альбома приходит
    # отдельным сообщением и попадает в collect_desc_photo.
    state.route_data[message.chat.id]["collecting"] = route_id
    _ask_more_photos(message.chat.id)


@bot.message_handler(
    content_types=["photo"],
    func=lambda m: state.route_data.get(m.chat.id, {}).get("collecting") is not None,
)
@require_registration
def collect_desc_photo(message):
    """Принимает дополнительные фотографии описания маршрута (в т.ч. альбомы)."""
    route_id = state.route_data[message.chat.id]["collecting"]
    count = _save_desc_photo(route_id, message)

    bot.send_message(
        message.chat.id,
        f"✅ Фото добавлено ({count}).\n"
        "Отправьте ещё фото или нажмите /done для завершения.",
    )


def _finish_route(chat_id):
    """Завершает создание маршрута."""
    route_name = state.route_data[chat_id]["name"]
    state.route_data.pop(chat_id, None)

    bot.send_message(
        chat_id,
        f"✅ Маршрут \"{route_name}\" добавлен!",
        reply_markup=admin_menu_keyboard(),
    )
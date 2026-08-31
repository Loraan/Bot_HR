"""Просмотр фотографий подтверждения (только для админов).

Flow:
1. Админ нажимает «Посмотреть фото»
2. Выбирает пользователя (только тех, у кого есть выполненные действия)
3. Выбирает маршрут (только те, где есть выполненные действия)
4. Выбирает действие (только выполненные)
5. Показывается фотография + подпись отдельным сообщением
"""

from telebot import types

from app import bot
from helpers.auth import is_admin, require_registration
from storage import photos as storage_photos
from storage import progress as storage_progress
from storage import routes as storage_routes
from storage import users as storage_users
import config


@bot.message_handler(func=lambda m: m.text == config.BTN_VIEW_PHOTOS)
@require_registration
def view_photos(message):
    """Начало просмотра фото: выбор пользователя."""
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ У вас недостаточно прав для этой операции.")
        return

    # Только пользователи, у которых выполнено хотя бы одно действие
    user_ids = storage_progress.users_with_progress()
    users = storage_users.load_users()

    keyboard = types.InlineKeyboardMarkup()
    added = False
    for user_id in user_ids:
        name, last_name = users.get(user_id, (str(user_id), ""))
        label = f"{name} {last_name}".strip()
        keyboard.add(types.InlineKeyboardButton(label, callback_data=f"photo_user:{user_id}"))
        added = True

    if not added:
        bot.send_message(message.chat.id, "📷 Пока нет пользователей с выполненными действиями.")
        return

    bot.send_message(
        message.chat.id,
        "👤 Выберите пользователя:",
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("photo_user:"))
def photo_choose_route(call):
    """Выбор маршрута после выбора пользователя."""
    user_id = int(call.data.split(":")[1])

    routes_with_progress = storage_progress.routes_with_progress(user_id)
    routes_list = storage_routes.load_routes()

    keyboard = types.InlineKeyboardMarkup()
    added = False
    for route_index in routes_with_progress:
        if route_index >= len(routes_list):
            continue
        name, _desc = routes_list[route_index]
        keyboard.add(
            types.InlineKeyboardButton(
                name, callback_data=f"photo_route:{user_id}:{route_index}"
            )
        )
        added = True

    bot.answer_callback_query(call.id)

    if not added:
        bot.edit_message_text(
            "У пользователя нет выполненных маршрутов.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
        )
        return

    bot.edit_message_text(
        "<b>Выберите маршрут:</b>",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("photo_route:"))
def photo_choose_task(call):
    """Выбор действия после выбора маршрута."""
    _, user_id, route_index = call.data.split(":")
    user_id = int(user_id)
    route_index = int(route_index)

    done_tasks = storage_progress.tasks_done(user_id, route_index)

    keyboard = types.InlineKeyboardMarkup()
    for task_index in done_tasks:
        task_name = config.ROUTE_TASKS[task_index]
        keyboard.add(
            types.InlineKeyboardButton(
                task_name, callback_data=f"photo_task:{user_id}:{route_index}:{task_index}"
            )
        )

    bot.answer_callback_query(call.id)

    if not done_tasks:
        bot.edit_message_text(
            "✅ В этом маршруте нет выполненных действий.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
        )
        return

    bot.edit_message_text(
        "✅ Выберите действие:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("photo_task:"))
def photo_show(call):
    """Показывает фотографию выбранного действия."""
    _, user_id, route_index, task_index = call.data.split(":")
    user_id = int(user_id)
    route_index = int(route_index)
    task_index = int(task_index)

    photo_paths = storage_photos.load_photos_by_task(user_id, route_index, task_index)

    bot.answer_callback_query(call.id)

    if not photo_paths:
        bot.edit_message_text(
            "📷 Фотография не найдена.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
        )
        return

    # Показываем фото (если их несколько — все)
    chat_id = call.message.chat.id
    for path in photo_paths:
        with open(path, "rb") as f:
            bot.send_photo(chat_id, f)

    # Подпись отдельным сообщением
    users = storage_users.load_users()
    name, last_name = users.get(user_id, (str(user_id), ""))
    author = f"{name} {last_name}".strip()

    routes_list = storage_routes.load_routes()
    route_name = routes_list[route_index][0] if route_index < len(routes_list) else "?"
    task_name = config.ROUTE_TASKS[task_index]

    bot.send_message(
        chat_id,
        f"👤 Пользователь: {author}\n"
        f"🗺️ Маршрут: {route_name}\n"
        f"✅ Действие: {task_name}",
    )
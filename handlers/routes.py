"""Callback-хендлеры маршрутов и выполнения заданий."""

from app import bot, state
from helpers.keyboards import main_menu_keyboard, route_detail_keyboard, routes_keyboard
from storage import photos as storage_photos
from storage import progress as storage_progress
from storage import routes as storage_routes
import config


def _is_route_completed(user_id: int, route_index: int) -> bool:
    """Проверяет, полностью ли выполнен маршрут пользователем."""
    completed = state.progress.get(user_id, {}).get("completed_routes", set())
    return route_index in completed


@bot.callback_query_handler(func=lambda call: call.data.startswith("route:"))
def show_route_detail(call):
    """Показывает описание выбранного маршрута с кнопками Назад и Выполнить."""
    index = int(call.data.split(":")[1])
    routes_list = storage_routes.load_routes()

    if index >= len(routes_list):
        bot.answer_callback_query(call.id, "Маршрут не найден")
        return

    bot.answer_callback_query(call.id)

    name, description = routes_list[index]
    user_id = call.from_user.id
    is_completed = _is_route_completed(user_id, index)

    text = f"🗺️ Маршрут: {name}\n\n{description}"
    if is_completed:
        text += "\n\n✅ Выполнен"

    bot.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=route_detail_keyboard(index),
    )


@bot.callback_query_handler(func=lambda call: call.data == "routes_back")
def routes_back(call):
    """Возвращает пользователя к выбору маршрута."""
    routes_list = storage_routes.load_routes()

    if not routes_list:
        bot.edit_message_text(
            "🗺️ Пока нет доступных маршрутов.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
        )
        return

    user_id = call.from_user.id
    completed = state.progress.get(user_id, {}).get("completed_routes", set())

    bot.edit_message_text(
        "🗺️ Доступные маршруты:\n\nВыберите маршрут:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=routes_keyboard(routes_list, completed),
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("do_route"))
def do_route(call):
    """Показывает меню с пунктами маршрута."""
    route_index = int(call.data.split(":")[1])
    user_id = call.from_user.id

    # Инициализируем прогресс пунктов для этого маршрута
    state.progress.setdefault(user_id, {}).setdefault(route_index, set())
    state.progress[user_id]["current_route"] = route_index

    bot.answer_callback_query(call.id)
    show_tasks_menu(call.message.chat.id, call.message.message_id, user_id, route_index)


def show_tasks_menu(chat_id, message_id, user_id: int, route_index: int):
    """Показывает меню с пунктами маршрута и кнопкой Назад."""
    done = state.progress.get(user_id, {}).get(route_index, set())

    text = "✅ Меню действий:\n\n"
    for i, task in enumerate(config.ROUTE_TASKS):
        mark = "✅" if i in done else "⬜"
        text += f"{mark} {task}\n"

    keyboard = _tasks_keyboard(route_index, done)

    if message_id is not None:
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard,
        )
    else:
        bot.send_message(chat_id, text, reply_markup=keyboard)


def _tasks_keyboard(route_index: int, done: set):
    """Клавиатура пунктов маршрута с отметками выполненности."""
    from telebot import types

    keyboard = types.InlineKeyboardMarkup()
    for i, task in enumerate(config.ROUTE_TASKS):
        label = ("✅ " if i in done else "") + task
        keyboard.add(types.InlineKeyboardButton(label, callback_data=f"task:{route_index}:{i}"))
    keyboard.row(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"route_back:{route_index}"))
    return keyboard


@bot.callback_query_handler(func=lambda call: call.data.startswith("route_back:"))
def route_back(call):
    """Возвращает из меню пунктов к описанию маршрута."""
    route_index = int(call.data.split(":")[1])
    routes_list = storage_routes.load_routes()

    if route_index < len(routes_list):
        name, description = routes_list[route_index]
        user_id = call.from_user.id
        is_completed = _is_route_completed(user_id, route_index)

        text = f"🗺️ Маршрут: {name}\n\n{description}"
        if is_completed:
            text += "\n\n✅ Выполнен"

        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=route_detail_keyboard(route_index),
        )
    else:
        # На случай если маршрут изменился - возвращаем к списку
        routes_list = storage_routes.load_routes()
        user_id = call.from_user.id
        completed = state.progress.get(user_id, {}).get("completed_routes", set())
        bot.edit_message_text(
            "🗺️ Доступные маршруты:\n\nВыберите маршрут:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=routes_keyboard(routes_list, completed),
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith("task:"))
def choose_task(call):
    """Начало выполнения выбранного пункта - просит загрузить 1 фотографию."""
    _, route_index, task_index = call.data.split(":")
    route_index = int(route_index)
    task_index = int(task_index)
    task_name = config.ROUTE_TASKS[task_index]

    state.progress.setdefault(call.from_user.id, {})["current_route"] = route_index

    # Сохраняем, что пользователь сейчас выполняет этот пункт
    state.photo_upload[call.message.chat.id] = (route_index, task_index)

    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        f"📸 Отправьте 1 фотографию для пункта \"{task_name}\":",
        reply_markup=_remove_keyboard(),
    )


def _remove_keyboard():
    from telebot import types

    return types.ReplyKeyboardRemove()


@bot.message_handler(content_types=["photo"], func=lambda m: m.chat.id in state.photo_upload)
def receive_photo(message):
    """Принимает фотографию и отмечает пункт выполненным."""
    route_index, task_index = state.photo_upload[message.chat.id]
    del state.photo_upload[message.chat.id]

    user_id = message.from_user.id
    task_name = config.ROUTE_TASKS[task_index]

    # Скачиваем и сохраняем фотографию подтверждения
    file_id = message.photo[-1].file_id  # берём самую большую версию фото
    file_info = bot.get_file(file_id)
    file_bytes = bot.download_file(file_info.file_path)
    storage_photos.save_photo(user_id, route_index, task_index, file_bytes)

    # Отмечаем пункт выполненным
    state.progress.setdefault(user_id, {}).setdefault(route_index, set()).add(task_index)
    storage_progress.save_progress(state)  # сохраняем прогресс в файл

    done = state.progress[user_id][route_index]
    all_done = len(done) == len(config.ROUTE_TASKS)

    if all_done:
        # Все пункты выполнены - маршрут считается выполненным
        state.progress[user_id].setdefault("completed_routes", set()).add(route_index)
        storage_progress.save_progress(state)
        bot.send_message(
            message.chat.id,
            "🎉 Маршрут полностью выполнен! Все пункты закрыты.",
            reply_markup=main_menu_keyboard(user_id),
        )
        return

    bot.send_message(
        message.chat.id,
        f"✅ Пункт \"{task_name}\" выполнен!",
        reply_markup=main_menu_keyboard(user_id),
    )

    # Показываем обновлённое меню с галочками
    show_tasks_menu(message.chat.id, None, user_id, route_index)

"""Хендлеры главного меню: рейтинговая таблица, маршруты, обратная связь."""

import config
from app import bot, state
from helpers import keyboards, scoring
from helpers.auth import is_admin, require_registration
from storage import feedback as storage_feedback
from storage import routes as storage_routes
from storage import users as storage_users


def show_main_menu(message):
    """Показывает главное меню с кнопками."""
    user_id = message.from_user.id
    bot.send_message(
        message.chat.id,
        "Пора посмотреть на город по новому, выбирай действие ниже:",
        reply_markup=keyboards.main_menu_keyboard(user_id),
    )


@bot.message_handler(func=lambda m: m.text == "Рейтинговая Таблица")
@require_registration
def rating_table(message):
    """Показывает рейтинговую таблицу участников по количеству баллов."""
    users = storage_users.load_users()

    if not users:
        bot.send_message(message.chat.id, "🏆 Пока нет ни одного участника.")
        return

    # Считаем баллы для всех, у кого есть прогресс
    scores = {}
    for user_id, user_data in state.progress.items():
        scores[user_id] = scoring.user_score(user_data)

    # Все зарегистрированные пользователи участвуют в рейтинге
    for user_id in users:
        scores.setdefault(user_id, 0)

    # Сортировка по убыванию баллов
    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    medals = ["🥇", "🥈", "🥉"]
    current_user_id = message.from_user.id

    lines = ["🏆 Рейтинговая таблица:\n"]
    for i, (user_id, score) in enumerate(ranking):
        name, last_name = users.get(user_id, (str(user_id), ""))
        full_name = f"{name} {last_name}".strip()

        # Медаль для первых трёх мест
        medal = medals[i] if i < 3 else f"{i + 1}."

        line = f"{medal} {full_name} — {score} б."
        # Выделяем текущего пользователя жирным (Markdown)
        if user_id == current_user_id:
            line = f"**{line}**"
        lines.append(line)

    bot.send_message(message.chat.id, "\n".join(lines), parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == "Маршруты")
@require_registration
def routes(message):
    """Показывает список доступных маршрутов."""
    routes_list = storage_routes.load_routes()

    if not routes_list:
        bot.send_message(message.chat.id, "🗺️ Пока нет доступных маршрутов.")
        return

    user_id = message.from_user.id
    completed = state.progress.get(user_id, {}).get("completed_routes", set())

    text = "<b>Доступные маршруты:</b>\n\nВыберите маршрут:"
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboards.routes_keyboard(routes_list, completed),
        parse_mode="HTML"
    )


@bot.message_handler(func=lambda m: m.text == "Обратная связь")
@require_registration
def feedback(message):
    """Приём обратной связи от пользователя (не для админов)."""
    user_id = message.from_user.id

    # Админам не нужно оставлять обратную связь
    if is_admin(user_id):
        bot.send_message(message.chat.id, "Вы администратор, обратная связь не требуется.")
        return

    # Пользователь должен быть зарегистрирован, чтобы назвать его по имени
    users = storage_users.load_users()
    if user_id not in users:
        bot.send_message(message.chat.id, "⚠️ Сначала зарегистрируйтесь через /start.")
        return

    bot.send_message(
        message.chat.id,
        "Поделитесь своими впечатлениями о работе бота или активностях цельным сообщением:",
        reply_markup=keyboards.cancel_keyboard(),
    )
    bot.register_next_step_handler(message, get_feedback)


@bot.message_handler(func=lambda m: m.text == "Админка")
@require_registration
def admin_menu(message):
    """Показывает меню админа."""
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ У вас недостаточно прав для этой операции.")
        return

    bot.send_message(
        message.chat.id,
        "🛠 Админка:",
        reply_markup=keyboards.admin_menu_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
def back_to_main_menu(message):
    """Возвращает в главное меню."""
    show_main_menu(message)


def get_feedback(message):
    """Получает текст обратной связи и сохраняет его в файл."""
    # Пользователь отменил отправку обратной связи
    if message.text == config.BTN_CANCEL:
        bot.send_message(
            message.chat.id,
            "🚫 Обратная связь отменена.",
            reply_markup=keyboards.main_menu_keyboard(message.from_user.id),
        )
        return

    if message.text is None or not message.text.strip():
        bot.send_message(
            message.chat.id,
            "Пожалуйста, отправьте обратную связь текстовым сообщением:",
            reply_markup=keyboards.cancel_keyboard(),
        )
        bot.register_next_step_handler(message, get_feedback)
        return

    user_id = message.from_user.id
    users = storage_users.load_users()
    first_name, last_name = users.get(user_id, ("", ""))

    feedback_text = message.text.strip()
    storage_feedback.save_feedback(user_id, first_name, last_name, feedback_text)

    bot.send_message(
        message.chat.id,
        "✅ Спасибо! Ваша обратная связь сохранена.",
        reply_markup=keyboards.main_menu_keyboard(user_id),
    )


@bot.message_handler(func=lambda m: m.text == "Посмотреть обратную связь")
def view_feedback(message):
    """Просмотр всей обратной связи (только для админов)."""
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ У вас недостаточно прав для этой операции.")
        return

    feedback_list = storage_feedback.load_feedback()

    if not feedback_list:
        bot.send_message(message.chat.id, "💬 Обратной связи пока нет.")
        return

    for _user_id, first_name, last_name, feedback_text in feedback_list:
        author = f"{first_name} {last_name}".strip() or "Неизвестный"
        bot.send_message(
            message.chat.id,
            f"💬 От: {author}\n\n{feedback_text}",
        )

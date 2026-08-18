"""Хендлеры главного меню: рейтинговая таблица, маршруты, обратная связь."""

from app import bot, state
from helpers import keyboards, scoring
from storage import routes as storage_routes
from storage import users as storage_users


def show_main_menu(message):
    """Показывает главное меню с кнопками."""
    user_id = message.from_user.id
    bot.send_message(
        message.chat.id,
        "Выберите действие:",
        reply_markup=keyboards.main_menu_keyboard(user_id),
    )


@bot.message_handler(func=lambda m: m.text == "Рейтинговая Таблица")
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

        line = f"{medal} {full_name} — {score} бал."
        # Выделяем текущего пользователя жирным (Markdown)
        if user_id == current_user_id:
            line = f"**{line}**"
        lines.append(line)

    bot.send_message(message.chat.id, "\n".join(lines), parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == "Маршруты")
def routes(message):
    """Показывает список доступных маршрутов."""
    routes_list = storage_routes.load_routes()

    if not routes_list:
        bot.send_message(message.chat.id, "🗺️ Пока нет доступных маршрутов.")
        return

    user_id = message.from_user.id
    completed = state.progress.get(user_id, {}).get("completed_routes", set())

    text = "🗺️ Доступные маршруты:\n\nВыберите маршрут:"
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboards.routes_keyboard(routes_list, completed),
    )


@bot.message_handler(func=lambda m: m.text == "Обратная связь")
def feedback(message):
    """Обратная связь."""
    # TODO: добавить логику — приём и сохранение обратной связи от участника
    bot.send_message(message.chat.id, "💬 Здесь можно оставить обратную связь.")

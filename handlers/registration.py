"""Хендлеры регистрации пользователей: /start и /users."""

from app import bot, state
from storage import users as storage_users
from handlers.menu import show_main_menu


@bot.message_handler(commands=["users"])
def show_users(message):
    """Показывает список всех зарегистрированных пользователей."""
    lines = storage_users.load_user_lines()

    if not lines:
        bot.send_message(message.chat.id, "Пока нет ни одного зарегистрированного пользователя.")
        return

    text = "📋 Список пользователей:\n\n"
    for i, line in enumerate(lines, 1):
        parts = line.split(" | ")
        if len(parts) == 3:
            user_id, name, last_name = parts
            text += f"{i}. {name} {last_name} (ID: {user_id})\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["start"])
def start(message):
    """Запускает регистрацию нового пользователя или приветствует уже зарегистрированного."""
    user_id = message.from_user.id

    if storage_users.user_exists(user_id):
        bot.send_message(message.chat.id, "Вы уже зарегистрированы! Добро пожаловать обратно 😊")
        show_main_menu(message)
        return

    # Начинаем регистрацию
    state.registration_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "Привет, коллега! 😃\n\n"
                                          "С новым кварталом к нам пришла новая активность, в разработке которой некоторые уже успели принять участие! Рассказываю, что тебя ждёт:\n\n"
                                          "📌 <b>Маршруты</b>\n"
                                          "Список готовых маршрутов по городу, включающий в себя прогулочную зону, место для перекуса и вариант активности на несколько часов\n\n"
                                          "📌 <b>Рейтинговая таблица</b>\n"
                                          "За каждое выполненное задание ты можешь получить 5 баллов. Чем больше выполнишь заданий, тем выше шанс попасть на лидерские позиции в рейтинге участников\n\n"
                                          "📌 <b>Обратная связь</b>\n"
                                          "Если ты нашел какую-то ошибку или обнаружил проблему при работе с ботом - смело сообщай об этом через обратную связь. А ещё можно просто написать приятные слова разработчикам, они обрадуются\n\n"
                                          "Готов? Тогда давай начинать!\n\n"
                                          "Напиши свои Фамилию и Имя 👇🏼",
                                          parse_mode="HTML")
    bot.register_next_step_handler(message, get_full_name)


def get_full_name(message):
    """Получает имя и фамилию и завершает регистрацию."""
    if message.text is None:
        bot.send_message(message.chat.id, "Пожалуйста, введите имя и фамилию текстом:")
        bot.register_next_step_handler(message, get_full_name)
        return

    split_name = message.text.split()
    state.registration_data[message.chat.id]["name"] = split_name[0].strip()
    state.registration_data[message.chat.id]["last_name"] = split_name[1].strip()

    user_id = message.from_user.id
    name = state.registration_data[message.chat.id]["name"]
    last_name = state.registration_data[message.chat.id]["last_name"]

    # Сохраняем в файл
    storage_users.save_user(user_id, name, last_name)

    # Очищаем временные данные
    state.registration_data.pop(message.chat.id, None)

    bot.send_message(
        message.chat.id,
        f"👋🏼 Привет, {name} {last_name}!",
    )
    show_main_menu(message)

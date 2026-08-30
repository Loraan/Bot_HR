"""Пакет хендлеров бота.

Импорт этого пакета регистрирует все обработчики на боте (через декораторы).
"""

# Импортируем модули, чтобы их декораторы зарегистрировали хендлеры на bot.
# menu импортируется первым, т.к. registration зависит от его show_main_menu.
from handlers import menu  # noqa: F401
from handlers import registration  # noqa: F401
from handlers import routes  # noqa: F401
from handlers import admin  # noqa: F401
from handlers import photos  # noqa: F401

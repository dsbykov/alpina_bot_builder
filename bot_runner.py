#!/usr/bin/env python3
"""
Скрипт для запуска Telegram-ботов из БД.
Запускает всех активных ботов, зарегистрированных в системе.
"""


import asyncio
import logging
import os
from asyncio.exceptions import CancelledError

import django
from asgiref.sync import sync_to_async

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot_builder.settings')
django.setup()
# Импорты моделей должны быть выполнены только после определения настроек Django

# fmt: off
# Исправление: отключение автоформатирования участка кода
from api.telegram_bot import start_bot
from api.models import Bot
# fmt: on

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@sync_to_async
def get_active_bots():
    return list(Bot.objects.filter(is_active=True))


async def main():
    """Основной цикл — запускает всех ботов из БД."""
    # Получаем активных ботов асинхронно
    active_bots = await get_active_bots()

    if not active_bots:
        logger.warning("Нет активных ботов в базе данных.")

    logger.info(f"Найдено {len(active_bots)} активных ботов. Запуск...")

    # Запускаем всех ботов параллельно
    bot_applications = []
    bot_running = []

    # Держим цикл активным
    try:
        while True:
            # Если бот активирован, но не запустился, запускаем его
            for bot in active_bots:
                if bot not in bot_running:
                    logger.info(f"Запускаю бота {bot.token[:10]}...")
                    app = await start_bot(bot.token)
                    if app:
                        bot_running.append(bot)
            # Если бот запущен, но дизактивирован, останавливаем его
            for bot in bot_running:
                if bot not in active_bots:
                    logger.info(f"Останавливаю бота {bot.token[:10]}...")
                    await bot_applications[bot_running.index(bot)].stop()
                    bot_running.remove(bot)
            await asyncio.sleep(60)  # Проверка раз в минуту
            logger.info("Проверка активности ботов каждую минуту...")

    except (KeyboardInterrupt, CancelledError):
        # Если выполнение скрипта остановлено с клавиатуры
        logger.info("Остановка ботов по запросу пользователя...")
        for app in bot_applications:
            await app.stop()
        logger.info("Все боты остановлены.")


if __name__ == '__main__':
    asyncio.run(main())

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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@sync_to_async
def get_active_bots():
    return list(Bot.objects.filter(is_active=True))


async def main():
    """Основной цикл — запускает всех ботов из БД."""

    # Запускаем всех ботов параллельно
    bot_running = {}

    # Держим цикл активным
    try:
        while True:
            # Получаем активных ботов асинхронно
            active_bots = await get_active_bots()

            # Если бот активирован, но не запустился, запускаем его
            if not active_bots:
                logger.warning("Нет активных ботов в базе данных.")
            else:
                logger.info(
                    f"Найдено {len(active_bots)} активных ботов. Запуск...")
                for bot in active_bots:
                    if bot not in bot_running.keys():
                        logger.info(f"Запускаю бота {bot.token}...")
                        app = await start_bot(bot.token)
                        if app:
                            logger.info(f"Бот {bot.name} запущен")
                            bot_running.update({bot: app})

            # Если бот запущен, но дизактивирован, останавливаем его
            for bot in bot_running.keys():
                if bot not in active_bots:
                    logger.info(
                        f"Останавливаю деактивированного бота {bot.token}...")
                    await bot_running[bot].stop()
                    bot_running.pop(bot)
            await asyncio.sleep(60)  # Проверка раз в минуту
            logger.info("Проверка активности ботов каждую минуту...")

    except (KeyboardInterrupt, CancelledError):
        # Если выполнение скрипта остановлено с клавиатуры
        logger.info("Остановка ботов по запросу пользователя...")
        for app in bot_running.keys():
            await bot_running[app].stop()
        logger.info("Все боты остановлены.")


if __name__ == '__main__':
    asyncio.run(main())

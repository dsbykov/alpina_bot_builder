import logging

from asgiref.sync import sync_to_async
from django.utils import timezone
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, \
    CommandHandler, CallbackContext

from .gigachat_client import get_gigachat_response_async
from .models import Bot, Scenario, Step, UserSession

logging.basicConfig(level=logging.INFO)


# Обертка для синхронных вызовов ORM
@sync_to_async
def get_bot_instance(token):
    return Bot.objects.filter(token=token, is_active=True).first()


@sync_to_async
def get_scenario(bot_id):
    return Scenario.objects.filter(bot_id=bot_id).first()


@sync_to_async
def get_steps(scenario_id):
    return Step.objects.filter(scenario_id=scenario_id).order_by("order")


@sync_to_async
def get_step_by_id(step_id, scenario_id):
    return Step.objects.filter(order=step_id, scenario_id=scenario_id).first()


@sync_to_async
def get_or_create_session(user_id, bot_instance):
    return UserSession.objects.get_or_create(
        user_id=user_id,
        bot=bot_instance
    )


@sync_to_async
def update_session(user_id, bot_instance, next_step_id):
    UserSession.objects.filter(
        user_id=user_id,
        bot=bot_instance
    ).update(
        current_step_id=next_step_id,
        last_activity=timezone.now()
    )


@sync_to_async
def delete_session(user_id, bot_instance):
    UserSession.objects.filter(user_id=user_id, bot=bot_instance).delete()


async def delete_session_handler(update: Update, context: CallbackContext):
    bot_instance = await get_bot_instance(context.bot.token)
    await delete_session(
        user_id=update.message.from_user.id,
        bot_instance=bot_instance
    )
    await update.message.reply_text("👌🏻")


async def help_menu(update: Update, context: CallbackContext):
    await update.message.reply_text(
        """Доступные команды:
        /help - Вызов этой справочной информации"
        /start - Выводит приветственное сообщение"
        /clear - Очищает данные сессии пользователя (сброс текущего шага 
        сценария)"""
    )


async def send_welcome_message(update: Update, context: CallbackContext):
    welcome_message = ("Привет! Я бот из учебного проекта."
                       "Начни диалог и посмотри что я могу")
    await update.message.reply_text(welcome_message)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id
    user_id = update.effective_user.id  # Уникальный ID пользователя Telegram

    logging.info(f"{chat_id} Написал боту: {user_message}")

    # Находим бот по токену
    bot_instance = await get_bot_instance(context.bot.token)
    if not bot_instance:
        logging.error(f"{chat_id} Ошибка: Бот не найден.")
        await update.message.reply_text("Бот не найден.")
        return

    # Берём первый сценарий и первый шаг
    scenario = await get_scenario(bot_instance.id)
    if not scenario:
        logging.error(f"{chat_id} Ошибка: Нет настроенных сценариев.")
        await update.message.reply_text("Нет настроенных сценариев.")
        return

    # 3. Получаем/создаём сессию пользователя
    session, _ = await get_or_create_session(user_id, bot_instance)
    current_step_id = session.current_step_id

    if current_step_id is None:
        # Начинаем с первого шага сценария
        steps = await get_steps(scenario.id)
        steps_list = await sync_to_async(list)(steps)
        if not steps_list:
            logging.error(f"{chat_id} Ошибка: Нет шагов в сценарии.")
            await update.message.reply_text("Нет шагов в сценарии.")
            return
        current_step = steps_list[0]
    else:
        # Получаем конкретный шаг по ID (через sync_to_async!)
        current_step = await get_step_by_id(current_step_id, scenario.id)
        if not current_step:
            logging.error(f"{chat_id} Текущий шаг {current_step} не найден.")
            await update.message.reply_text("Ошибка: шаг не найден.")
            # В случае ошибки сбрасываем состояние сессии, чтобы избежать
            # зацикливания
            await delete_session(user_id, bot_instance)
            return

    # 4. Формируем промт и отправляем в GigaChat
    prompt = current_step.prompt.format(user_message=user_message)
    gigachat_response = await get_gigachat_response_async(prompt)

    logging.info(f"{chat_id} Ответ бота: {gigachat_response}")
    await update.message.reply_text(gigachat_response)

    # 5. Переходим к следующему шагу
    next_step_id = current_step.next_step_id
    if next_step_id:
        # Обновляем сессию пользователя
        await update_session(user_id, bot_instance, next_step_id)
    else:
        # Сценарий завершён — удаляем сессию
        await delete_session(user_id, bot_instance)
        await update.message.reply_text("Хотите узнать гороскоп кого-то еще?.")


async def start_bot(token: str):
    """Запускает один Telegram-бот."""
    try:
        application = Application.builder().token(token).build()

        application.add_handler(CommandHandler("help", help_menu))
        application.add_handler(CommandHandler("start", send_welcome_message))
        application.add_handler(CommandHandler(
            "clear", delete_session_handler))

        await application.initialize()
        await application.updater.initialize()

        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )

        logging.info(f"Запуск бота с токеном ...{token[-9:]}")
        await application.start()
        await application.updater.start_polling()
        return application
    except Exception as e:
        logging.error(f"Ошибка при запуске бота ...{token[-9:]}: {e}")
        return None

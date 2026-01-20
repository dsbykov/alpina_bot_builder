import logging

from asgiref.sync import sync_to_async
from django.utils import timezone
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, \
    CommandHandler, CallbackContext

from .gigachat_client import get_gigachat_response_async
from .models import Bot, Scenario, Step, UserSession

logging.basicConfig(level=logging.DEBUG)


# Обертка для синхронных вызовов ORM
@sync_to_async
def get_bot_instance(token):
    logging.debug(f"Получаем бота по токену ...{token[-9:]}")
    bot = Bot.objects.filter(token=token, is_active=True).first()
    logging.debug(f"Бот найден: {bot.id}")
    return bot


@sync_to_async
def get_scenario(bot_id):
    logging.debug(f"Получаем сценарий для бота {bot_id}")
    return Scenario.objects.filter(bot_id=bot_id).first()


@sync_to_async
def get_steps(scenario: Scenario):
    logging.debug(f"Получаем шаги для сценария {scenario.id}")
    return scenario.steps.all().order_by("order")


@sync_to_async
def get_step_by_id(step_id, scenario_id):
    logging.debug(f"Получаем шаг {step_id} для сценария {scenario_id}")
    try:
        return Step.objects.get(id=step_id, scenario_id=scenario_id)
    except Step.DoesNotExist:
        logging.warning(
            f"Шаг {step_id} для сценария {scenario_id} не найден"
        )
        return None


@sync_to_async
def get_next_step(current_step: Step, scenario: Scenario):
    if current_step.next_step_id:
        logging.debug(
            f"Следующий шаг: {current_step.next_step_id.pk}"
        )
        next_step = Step.objects.get(pk=current_step.next_step_id.pk)
        logging.debug(f"Следующий шаг определен успешно: {next_step.pk}")
        return next_step
    else:
        logging.warning("Определяю следующий шаг альтернативным способом")
        return scenario.steps.filter(order__gt=current_step.pk).first()


@sync_to_async
def get_steps_info(scenario: Scenario):
    """Возвращает: (есть_ли_шаги: bool, первый_шаг: Step или None)."""
    logging.debug(f"Получаем информацию о шагах для сценария {scenario.id}")
    steps = scenario.steps.all().order_by("order")
    if steps.exists():
        logging.debug(
            f"Шаги найдены: {steps.count()}"
        )
        return True, steps.first()
    logging.debug("Шаги не найдены")
    return False, None


@sync_to_async
def get_or_create_session(user_id, bot_instance):
    logging.debug(
        f"Получаем или создаём сессию для пользователя {user_id} и бота {bot_instance.id}"
    )
    return UserSession.objects.get_or_create(
        user_id=user_id,
        bot=bot_instance
    )


@sync_to_async
def update_session(user_id, bot_instance, next_step_id):
    logging.info("Обновляем сессию пользователя")
    logging.debug(
        f"Пользователь {user_id}\n"
        f"бот {bot_instance.id}\n"
        f"следующий шаг {next_step_id}"
    )
    UserSession.objects.filter(
        user_id=user_id,
        bot=bot_instance
    ).update(
        current_step_id=next_step_id,
        last_activity=timezone.now(),
    )
    logging.debug('Сессия успешно обновлена')


@sync_to_async
def delete_session(user_id, bot_instance):
    logging.info("Удаляем сессию пользователя")
    UserSession.objects.filter(user_id=user_id, bot=bot_instance).delete()
    logging.debug("Сесси пользователя успешно удалена")


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
    logging.debug(
        f"Берём первый сценарий и первый шаг для бота {bot_instance.id}")
    scenario = await get_scenario(bot_instance.id)
    if not scenario:
        logging.error(f"{chat_id} Ошибка: Нет настроенных сценариев.")
        await update.message.reply_text("Нет настроенных сценариев.")
        return

    # 3. Получаем/создаём сессию пользователя
    session, _ = await get_or_create_session(user_id, bot_instance)
    current_step_id = session.current_step_id
    logging.debug(f"Текущий шаг: {current_step_id}")

    if current_step_id is None:
        logging.debug("У пользователя нет незавершённого сценария")
        has_steps, current_step = await get_steps_info(scenario)
        if not has_steps:
            logging.error(f"{chat_id} Ошибка: Нет шагов в сценарии.")
            await update.message.reply_text("Нет шагов в сценарии.")
            return
        logging.debug("Записываем в 'текущий' первый шаг сценария")
        await update_session(user_id, bot_instance, current_step.pk)
        logging.debug(f"Текущий шаг {current_step}")
    else:
        current_step = await get_step_by_id(current_step_id, scenario.id)
        logging.debug(f"Текущий шаг {current_step}")
        if not current_step:
            logging.error(
                f"Чат:{chat_id}, текущий шаг {current_step_id} не найден")
            await update.message.reply_text("Ошибка: шаг не найден.")
            # В случае ошибки сбрасываем состояние сессии, чтобы избежать
            # зацикливания
            await delete_session(user_id, bot_instance)
            return

    # 4. Формируем промт и отправляем в GigaChat
    # logging.debug(f"Формируем промт для шага {current_step}")
    prompt = current_step.prompt.format(user_message=user_message)
    logging.debug(f"Промт: {prompt}")
    gigachat_response = await get_gigachat_response_async(prompt)

    logging.info(f"{chat_id} Ответ бота: {gigachat_response}")
    await update.message.reply_text(gigachat_response)

    # 5. Переходим к следующему шагу
    logging.info("Переходим к следующему шагу")
    logging.debug(f"current_step: {current_step}")
    next_step_id = await get_next_step(current_step, scenario)
    if next_step_id:
        # Обновляем сессию пользователя
        # logging.info("Обновляем сессию пользователя")
        # logging.debug(f"Пользователь {user_id}, на шаг {next_step_id}")
        await update_session(user_id, bot_instance, next_step_id.pk)
    else:
        # Сценарий завершён — удаляем сессию
        logging.debug(f"Сбрасываем состояние сессии для {user_id}")
        await delete_session(user_id, bot_instance)
        logging.info("Сценарий завершён")
        await update.message.reply_text("Хотите узнать гороскоп кого-то еще?.")


async def error_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработчик ошибок бота."""
    logging.error("Exception while handling an update:",
                  exc_info=context.error)

    # Дополнительно: можно отправить сообщение пользователю
    if update and update.effective_user:
        try:
            await update.effective_chat.send_message(
                "Что-то пошло не так..."
            )
        except:
            pass  # Игнорировать ошибки при отправке сообщения об ошибке


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

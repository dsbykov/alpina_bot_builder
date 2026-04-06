import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def save_user_details(backend, user, response, *args, **kwargs):
    """
    Сохраняет first_name и last_name из профиля Яндекса.
    """
    if backend.name == 'yandex-oauth2':
        # Пример данных из response:
        # {
        #   "id": "12345",
        #   "first_name": "Иван",
        #   "last_name": "Иванов",
        #   "display_name": "Иван Иванов"
        # }

        changed = False
        logger.debug('Созранение данных из Яндекс АйДи')
        # ← ключевая строка
        logger.info(f'Полный ответ от Яндекса: {response}')

        # Сохраняем имя
        first_name = response.get('first_name')
        logger.debug(f"Имя из ответа: {first_name}")
        logger.debug(f"Имя из модели: {user.first_name}")
        if first_name and not user.first_name:
            user.first_name = first_name
            changed = True
            logger.debug(f"Имя сохранено: {first_name}")

        # Сохраняем фамилию
        last_name = response.get('last_name')
        logger.debug(f"Фамилия из ответа: {last_name}")
        logger.debug(f"Фамилия из модели: {user.last_name}")
        if last_name and not user.last_name:
            user.last_name = last_name
            changed = True
            logger.debug(f"Фамилия сохранена: {last_name}")

        # Обновляем, чтобы было всегда актуальное имя
        if user.first_name != first_name:
            user.first_name = first_name or user.first_name
            changed = True
            logger.debug(f'обновлем данные из яндекса {first_name}')

        if user.last_name != last_name:
            user.last_name = last_name or user.last_name
            changed = True
            logger.debug(f'обновлем данные из яндекса {last_name}')

        if changed:
            user.save()
            logger.debug('Данные из яндекса сохранены')
        else:
            logger.debug('Изменений в данных пользователя нет')

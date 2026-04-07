import logging

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
        logger.debug('Сохранение данных из Яндекс АйДи')
        # ← ключевая строка

        first_name = response.get('first_name')
        last_name = response.get('last_name')

        # Сохраняем имя
        logger.info(f"Пользователь '{first_name} {last_name}'"
                    " успешно авторизован")
        if first_name and not user.first_name:
            user.first_name = first_name
            changed = True
            logger.debug(f"Добавляем имя пользователя: {first_name}")

        # Сохраняем фамилию

        logger.debug(f"Фамилия из ответа: {last_name}")
        if last_name and not user.last_name:
            user.last_name = last_name
            changed = True
            logger.debug(f"Добавляем фамилию "
                         "пользователя: {last_name}")

        # Обновляем, чтобы было всегда актуальное имя
        if user.first_name != first_name:
            user.first_name = first_name or user.first_name
            changed = True
            logger.debug(f'Обновлем имя пользователя {first_name}')

        if user.last_name != last_name:
            user.last_name = last_name or user.last_name
            changed = True
            logger.debug(f'Обновлем фамилию пользователя {last_name}')

        if changed:
            user.save()
            logger.debug(f'Учетные данные пользователя {first_name} '
                         f'{last_name} сохранены')
        else:
            logger.debug(f'Учетные данные пользователя {first_name} '
                         f'{last_name} не требуют изменений')

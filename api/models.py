# models.py
from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
import logging
from .crypto import get_encryption_key, encrypt_token, decrypt_token


logger = logging.getLogger(__name__)


class Bot(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя бота")
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
    )
    description = models.TextField(blank=True)
    # Хранится в зашифрованном виде
    token = models.TextField(verbose_name="Telegram Bot Token", max_length=255)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Шифрует токен перед сохранением, если он ещё не зашифрован.
        """
        logger.debug(f"Сохраняю данные бота (ID: {self.pk})")
        # Проверяем, новый ли объект или токен уже зашифрован
        if self.pk is None or not self._is_encrypted():
            logger.info(
                f"Шифруем токен для бота '{self.token}' (ID: {self.pk})")
            plain_token = self.token
            self.token = encrypt_token(plain_token)

        super().save(*args, **kwargs)

    def _is_encrypted(self):
        """
        Проверяет, является ли значение `token` уже зашифрованным.
        Пробуем расшифровать — если получается, значит зашифровано.
        """
        try:
            f = Fernet(get_encryption_key())
            f.decrypt(self.token.encode('utf-8'))
            logger.debug(
                f"Токен для бота '{self.token}' (ID: {self.pk}) уже зашифрован")
            return True
        except Exception:
            logger.debug(
                f"Токен для бота '{self.token}' (ID: {self.pk}) не зашифрован")
            return False

    def get_token(self):
        """
        Возвращает расшифрованный токен.
        """
        return decrypt_token(self.token)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Telegram Бот"
        verbose_name_plural = "Telegram Боты"


class Scenario(models.Model):
    bot = models.ForeignKey(
        to=Bot,
        on_delete=models.CASCADE,
        related_name='scenarios',
        null=True,
    )
    title = models.CharField(max_length=100)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    def __str__(self):
        return f"{self.title} ({self.bot.name})"

    class Meta:
        verbose_name = "Сценарий"
        verbose_name_plural = "Сценарии"


class Step(models.Model):
    scenario = models.ForeignKey(
        Scenario,
        on_delete=models.CASCADE,
        related_name='steps',
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
    )
    order = models.PositiveIntegerField()
    prompt = models.TextField()  # Что отправляем в GigaChat
    response_template = models.TextField(blank=True)  # Шаблон ответа
    next_step_id = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_step',
    )

    def __str__(self):
        return f"""
            id: {self.pk}
            Step order: {self.order}
            prompt: {self.prompt}
        """

    class Meta:
        ordering = ['order']
        verbose_name = "Шаг"
        verbose_name_plural = "Шаги"


class UserSession(models.Model):
    user_id = models.BigIntegerField()  # Telegram user_id
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    current_step_id = models.IntegerField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user_id', 'bot')  # Один сеанс на пользователя

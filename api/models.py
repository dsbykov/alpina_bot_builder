from django.db import models


class Bot(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    token = models.CharField(max_length=200, unique=True)  # Telegram bot token
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Scenario(models.Model):
    bot = models.ForeignKey(
        to=Bot,
        on_delete=models.CASCADE,
        related_name='scenarios',
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    def __str__(self):
        return f"{self.title} ({self.bot.name})"


class Step(models.Model):
    scenario = models.ForeignKey(
        Scenario,
        on_delete=models.CASCADE,
        related_name='steps',
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

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"""
            id: {self.pk}
            Step order: {self.order}
            prompt: {self.prompt}
        """


class UserSession(models.Model):
    user_id = models.BigIntegerField()  # Telegram user_id
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    current_step_id = models.IntegerField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user_id', 'bot')  # Один сеанс на пользователя

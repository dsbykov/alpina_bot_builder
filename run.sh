#!/usr/bin/env sh

set -e  # Прекращать выполнение при любой ошибке

# Конфигурация логов
LOG_DIR="/tmp/logs"
mkdir -p "$LOG_DIR"
exec >> "$LOG_DIR/startup.log" 2>&1

echo "=== Запуск приложения $(date) ===" | tee /dev/fd/2

# Функция для логирования с выводом в консоль
log() {
  echo "$1" | tee -a "$LOG_DIR/startup.log" /dev/fd/2
}

error() {
  echo "ERROR: $1" | tee -a "$LOG_DIR/startup.log" /dev/fd/2 >&2
  exit 1
}

# Проверка наличия переменных окружения
if [ -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
    error "Ошибка: DJANGO_SUPERUSER_PASSWORD не задан!"
    exit 1
fi

if [ -z "$DJANGO_SUPERUSER_EMAIL" ]; then
    error "Ошибка: DJANGO_SUPERUSER_EMAIL не задан!"
    exit 1
fi

if [ -z "$GIGACHAT_AUTH_KEY" ]; then
    error "Ошибка: GIGACHAT_AUTH_KEY не задан!"
    exit 1
fi

# 1. Миграции
log "Выполняю миграции..."
python manage.py migrate --noinput

# 2. Создание суперпользователя (только если его ещё нет)
log "Создаю суперпользователя..."
python manage.py shell <<EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        password='$DJANGO_SUPERUSER_PASSWORD',
        email='$DJANGO_SUPERUSER_EMAIL'
    )
    print("Суперпользователь создан '$DJANGO_SUPERUSER_PASSWORD'")
else:
    print("Суперпользователь уже существует")
EOF

# 3. Запуск Django-сервера (Gunicorn)
log "Запускаю Django-сервер..."
# gunicorn bot_builder.wsgi:application \
#   --bind 127.0.0.1:8000 \
#   --workers 4 \
#   --timeout 120 \
#   --log-file "$LOG_DIR/gunicorn.log" \
#   --error-logfile "$LOG_DIR/gunicorn_error.log" &
python manage.py runserver 0.0.0.0:8000



# Сохраняем PID сервера
GUNICORN_PID=$!


# 4. Проверка готовности сервера
log "Ожидаю готовности Django-сервера..."
for i in {1..30}; do
  if curl -s http://127.0.0.1:8000/admin/login/ > /dev/null; then
    log "Django-сервер готов"
    break
  fi
  error "Попытка $i/30: сервер не отвечает..."
  sleep 2
done

if ! curl -s http://127.0.0.1:8000/admin/login/ > /dev/null; then
  error "Ошибка: Django-сервер не запустился за 60 секунд"
  kill $GUNICORN_PID || true
  exit 1
fi

# 5. Запуск ботов
log "Запускаю ботов..."
nohup python bot_runner.py \
  >> "$LOG_DIR/bot.log" 2>&1 &

BOT_PID=$!

# 6. Мониторинг процессов
log "Все сервисы запущены. PID: Gunicorn=$GUNICORN_PID, Бот=$BOT_PID"

# Ожидание завершения ботов (опционально)
# wait $BOT_PID

# Если нужно останавливать всё при падении бота:
# while ps -p $BOT_PID > /dev/null; do sleep 1; done
# kill $GUNICORN_PID



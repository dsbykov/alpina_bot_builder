#!/bin/sh
set -e  # Переносим в начало!

echo "=== DEBUG INFO ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python --version 2>&1)"

# Проверка Gunicorn
if command -v gunicorn >/dev/null 2>&1; then
    echo "Gunicorn version: $(gunicorn --version)"
else
    echo "Gunicorn: NOT INSTALLED"
fi

echo "Environment variables (using printenv):"
printenv

echo "Files in current directory (using find):"
find . -maxdepth 1 -type f -o -type d

echo "====================="

# Конфигурация логов
LOG_DIR="/tmp/logs"
echo "Создание директории логов: $LOG_DIR"
mkdir -p "$LOG_DIR"

echo "Проверяем создание директории"
if [ ! -d "$LOG_DIR" ]; then
    echo "ERROR: Failed to create log directory $LOG_DIR"
    exit 1
fi

echo "Проверяем права доступа к новой директории"
if [ ! -w "$LOG_DIR" ]; then
    echo "ERROR: No write permission in $LOG_DIR"
    exit 1
fi

# echo "Перенаправление вывода в $LOG_DIR/startup.log"
# exec >> "$LOG_DIR/startup.log" 2>&1
# echo "Вывод перенаправлен"

echo "=== Запуск приложения $(date) ==="

# echo "Создание функций логирования"
# # Функция для логирования с выводом в консоль
# log() {
#     echo "$(date): $1" | tee -a "$LOG_DIR/startup.log"
# }

# error() {
#     echo "$(date): ERROR: $1" | tee -a "$LOG_DIR/startup.log" >&2
#     exit 1
# }

# Проверка наличия переменных окружения
if [ -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Ошибка: DJANGO_SUPERUSER_PASSWORD не задан!"
fi

if [ -z "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Ошибка: DJANGO_SUPERUSER_EMAIL не задан!"
fi

if [ -z "$GIGACHAT_AUTH_KEY" ]; then
    echo "Ошибка: GIGACHAT_AUTH_KEY не задан!"
fi

if [ -z "$DJANGO_SECRET_KEY" ]; then
     echo "Ошибка: DJANGO_SECRET_KEY не задан!"
fi

# 1. Миграции
echo "Выполняю миграции..."
python manage.py migrate --noinput || {
    echo "Ошибка: Миграции не выполнены!"
    exit 1
}

# 2. Сбор статики
echo "Собираю статические файлы..."
python manage.py collectstatic --noinput || {
    echo "Ошибка: Не удалось собрать статику!"
    exit 1
}

# 3. Создание суперпользователя (только если его ещё нет)
echo "Создаю суперпользователя..."
python manage.py shell <<EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        password='$DJANGO_SUPERUSER_PASSWORD',
        email='$DJANGO_SUPERUSER_EMAIL'
    )
    print("Суперпользователь создан")
else:
    print("Суперпользователь уже существует")
EOF

# 3. Запуск Django-сервера (Gunicorn)
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "Запускаю Django-сервер на WSGI..."
    exec gunicorn bot_builder.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 4 \
        --timeout 120 \
        --log-file "$LOG_DIR/gunicorn.log" \
        --error-logfile "$LOG_DIR/gunicorn_error.log"
elif [ "$ENVIRONMENT" = "dev" ]; then
    echo "Запускаю Django-сервер на отладке..."
    python manage.py runserver 0.0.0.0:8000
else
    echo "!!! RUN.SH ERROR: Переменная ENVIRONMENT может быть только 'prod' или 'dev', а сейчас она равна '$ENVIRONMENT'"
    exit 1
fi

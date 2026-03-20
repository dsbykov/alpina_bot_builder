# Alpina Bot Builder 🤖

Учебный проект от компании «Alpina Digital» — API для создания и управления Telegram-ботами с использованием GPT (через GigaChat).

Проект включает:
- REST API на Django + DRF
- Интеграцию с GigaChat API
- Поддержку сценариев диалога
- Админ-панель для управления ботами
- Автоматический деплой через GitHub Actions
- Работу за Nginx + Let's Encrypt (HTTPS)

---

## 🛠 Локальная настройка (для разработки)

### Предварительные требования
- Python 3.10+
- PostgreSQL
- `pip`, `virtualenv`
- `openssl` (для генерации ключей)

### Шаги установки

1. Клонировать репозиторий
    ```bash
   git clone https://github.com/your-username/alpina_bot_builder.git
   cd alpina_bot_builder
   ```
2. Создать виртуальное окружение
   ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # или
    .venv\Scripts\activate     # Windows
   ```
3. Установить зависимости: 
   ```bash
   pip install -r requirements.txt
   ```
4. Выполнить миграции: 
   ```bash
   python manage.py migrate
   ```
5. Создать суперпользователя: 
   ```bash
   python manage.py createsuperuser
   ```
6. Создать в корне проекта файл: `.env`
   ```bash
    DJANGO_SECRET_KEY=''
    GIGACHAT_AUTH_KEY=''
    FERNET_KEY='' # Ключ шифрования чувствительных данных (Смотри "Генерация FERNET_KEY")

    DEBUG='True'
    ENVIRONMENT='dev' # prod or dev

    POSTGRES_HOST='localhost'
    POSTGRES_DB='bot_builder_db'    
    POSTGRES_USER='postgres'
    POSTGRES_PASSWORD='your_password'
    PGUSER='postgres'

    CSRF_TRUSTED_ORIGINS='http://localhost:8000'
    ALLOWED_HOSTS='0.0.0.0 127.0.0.1 127.0.0.1:8000 django 45.155.204.67'

    DJANGO_SUPERUSER_PASSWORD='admin'
    DJANGO_SUPERUSER_EMAIL='my_email@yandex.ru'

    DJANGO_SETTINGS_MODULE='bot_builder.settings'
   ``` 
7. Запустить сервер: 
    ```bash
   python manage.py runserver 0.0.0.0:8000
   ``` 
8.  Запустить шендлер ботов: 
   ```bash
   python bot_runner.py
   ```

🔍 Откройте: http://127.0.0.1:8000

Админка: http://127.0.0.1:8000/admin

### 🔐 Генерация FERNET_KEY

Выполните в Python-интерпретаторе:

```python
from cryptography.fernet import Fernet
print(Fornet.generate_key())
```

Скопируйте вывод в .env как значение FERNET_KEY.

## 🚀 Деплой на VPS (Ubuntu/Debian)

Деплой выполняется автоматически через github Actions, инструкции для которого располоены в файле .github\workflows\build.yml

Для старта проекта необходимо на удаленной виртуальной машине (VPS): 

1. Создайте директорию проекта:
   ```bash
    mkdir -p ~/django && cd ~/django
   ```
2. Скопируйте туда:
   * docker-compose.yml
   * nginx.conf
   * .env (с продакшен-настройками)
3. Обновите в nginx.conf:
```bash
server_name your-domain.ru;  # ← ваш домен
```
4. Установите Certbot и получите SSL-сертификат:
   ```bash
    sudo apt update && sudo apt install certbot -y
    sudo mkdir -p /var/www/certbot
    sudo certbot certonly --webroot -w /var/www/certbot -d your-domain.ru
   ```
5. Настройте автобновление сертификатов:
   ```bash
    sudo crontab -e
   ``` 
6. Добавьте строку:
   ```bash
   0 12 * * * /usr/bin/certbot renew --quiet && docker-compose -f /путь/до/docker-compose.yml restart nginx
   ```
7. Запустите проект:
   ```bash
    docker compose up -d
   ```

✅ Проект будет доступен по:

👉 https://your-domain.ru

---

## 📦 Стек технологий


| Компонент	      | Технология | 
| ---------       | ---------- |
| Backend         | Django 5.2, Django REST Framework |
| База данных     | PostgreSQL 15 |
| Контейнеризация | Docker, Docker Compose |
| Веб-сервер      | Nginx |
| SSL             | Let's Encrypt + Certbot |
| CI/CD           | GitHub Actions |
| Хранение ключей | Fernet (cryptography) |

---

## 🔄 CI/CD (GitHub Actions)

Деплой выполняется автоматически при merge PR в ветку main. (После успешного прохождения условного ревью кода)

Конфигурация: `.github/workflows/build.yml`

---

## 🧪 Доступные эндпоинты (API)

* GET /api/bots/ — список ботов
* POST /api/bots/ — создать бота
* GET /api/scenarios/ — сценарии
* POST /api/scenarios/ — создать сценарий
* GET /api/steps/ — список шагов
* POST /api/steps/ — создать шаг

---

## 📂 Структура проекта

```bash
alpina_bot_builder/
├── bot_builder/        # Настройки Django
├── api/                # REST API
├── bots/               # Логика ботов
├── bot_runner.py       # Запуск обработчика Telegram
├── docker-compose.yml
├── nginx.conf
├── requirements.txt
└── README.md
```

---

## ❓ Проблемы и решения

| Проблема  | Решение |
| --------- | ------- |
| DisallowedHost | Проверьте ALLOWED_HOSTS (без запятых!) |
| Invalid HTTP_HOST header | Используйте http://..., а не https:// при runserver |
| Permission denied к сертификатам | Убедитесь, что Nginx запущен от root |
| Certbot 404 | Проверьте монтирование /var/www/certbot и location в Nginx |

---

## 🙌 Благодарности

Проект реализован в рамках образовательной программы "Python разработчик 2.0" от ProductStar.

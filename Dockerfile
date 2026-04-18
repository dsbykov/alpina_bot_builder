FROM python:3.12-alpine

# Установка зависимостей
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV STATIC_ROOT=/app/staticfiles
ENV MEDIA_ROOT=/app/media
ENV LOGS_DIR=/app/logs
ENV DJANGO_SETTINGS_MODULE=bot_builder.settings

RUN addgroup -g 1000 appgroup && \
    adduser -D -u 1000 -G appgroup appuser


WORKDIR /app

COPY ./api ./api
COPY ./bot_builder ./bot_builder
COPY ./data ./data
COPY ./templates ./templates
COPY manage.py .
COPY requirements.txt .
COPY bot_runner.py .
COPY ./run.sh .

RUN mkdir -p /app/logs && chown -R appuser:appgroup /app/logs


RUN python -m pip install --upgrade pip --no-warn-script-location
RUN pip install --no-cache-dir -r requirements.txt --no-warn-script-location

RUN chown -R appuser:appgroup /app

USER appuser

# Сбор статики
RUN python manage.py collectstatic --noinput


EXPOSE 8000

CMD [ "sh", "run.sh" ]
FROM python:3.12-alpine

RUN pip install --upgrade pip
RUN pip install --no-cache-dir uv

WORKDIR /alpina_bot_builder

COPY ./api ./api
COPY ./bot_builder ./bot_builder
COPY ./data ./data
COPY manage.py .
COPY uv.lock .
COPY bot_runner.py .
COPY ./run.sh .

RUN uv sync --system


RUN adduser -D appuser
USER appuser

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD [ "sh", "run.sh" ]
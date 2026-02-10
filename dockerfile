FROM python:3.12-alpine

# RUN adduser -D appuser
# USER appuser

WORKDIR /alpina_bot_builder

COPY ./api ./api
COPY ./bot_builder ./bot_builder
COPY ./data ./data
COPY manage.py .
COPY requirements.txt .
COPY bot_runner.py .
COPY ./run.sh .
# COPY ./run_debug.sh .


RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt




EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000" ]
CMD [ "sh", "run.sh" ]
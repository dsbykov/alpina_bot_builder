FROM python:3.12-alpine


RUN addgroup -g 1000 appgroup && \
    adduser -D -u 1000 -G appgroup appuser
USER appuser


WORKDIR /alpina_bot_builder

COPY ./api ./api
COPY ./bot_builder ./bot_builder
COPY ./data ./data
COPY manage.py .
COPY requirements.txt .
COPY bot_runner.py .
COPY ./run.sh .


RUN python -m pip install --upgrade pip --no-warn-script-location
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD [ "sh", "run.sh" ]
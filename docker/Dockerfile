FROM python:3.13-alpine

ENV APP_DIR=/app
WORKDIR ${APP_DIR}

RUN apk update && apk add linux-headers \
    python3-dev \
    gcc \
    libc-dev \
    libpq-dev

COPY poetry.lock pyproject.toml README.md ${APP_DIR}/
COPY path_tmpl_worker/ ${APP_DIR}/path_tmpl_worker/

RUN pip install --upgrade poetry

COPY poetry.lock pyproject.toml app/
RUN poetry install -E pg

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

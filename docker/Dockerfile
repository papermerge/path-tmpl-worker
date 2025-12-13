# Build stage - compile dependencies
FROM python:3.14-alpine AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    libc-dev \
    linux-headers \
    libpq-dev \
    python3-dev

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY path_tmpl_worker ./path_tmpl_worker
COPY README.md ./

# Install the project
RUN uv sync --frozen --no-dev

# Runtime stage - minimal image
FROM python:3.14-alpine

ENV APP_DIR=/app \
    PATH="/app/.venv/bin:$PATH"

# Install only runtime dependencies
RUN apk add --no-cache \
    libpq \
    && apk upgrade --no-cache \
    && rm -rf /var/cache/apk/*

WORKDIR ${APP_DIR}

# Copy virtual environment and application from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/path_tmpl_worker /app/path_tmpl_worker

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

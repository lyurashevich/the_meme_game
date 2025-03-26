FROM python:3.13-slim-bookworm AS base

RUN pip install --no-cache-dir uv==0.6.9 && \
    apt-get update && apt-get install -y --no-install-recommends curl=7.88.1-10+deb12u12 && \
    uv venv /opt/venv && \
    rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY requirements.lock .

RUN uv pip install --no-cache-dir -r requirements.lock

COPY src .

EXPOSE 8000

CMD ["sh", "-c", "gunicorn --workers $((2 * $(nproc))) meme_game.wsgi:application --bind 0.0.0.0:8000"]

FROM base AS tests

WORKDIR /app

RUN set -e && apt-get update && \
    apt-get install -y --no-install-recommends git=1:2.39.5-0+deb12u2 && \
    uv pip install --no-cache-dir pip-tools==7.4.1 pre-commit==4.1.0 && \
    rm -rf /var/lib/apt/lists/* && \
    git config --global --add safe.directory /app

COPY requirements-tests.lock ./

RUN uv pip install --no-cache-dir -r requirements-tests.lock

CMD ["sh", "-c", "python manage.py migrate && pytest"]
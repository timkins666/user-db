FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml uv.lock ./

WORKDIR /app/backend-fastapi

COPY backend-fastapi/pyproject.toml .

RUN uv sync

COPY ./backend-fastapi/src/. ./src/

ENV PYTHONPATH=/app/backend-fastapi/src

EXPOSE 80

CMD ["/app/.venv/bin/uvicorn", "userdb.main:app", "--host", "0.0.0.0", "--port", "80",  "--reload", "--reload-dir", "/app"]

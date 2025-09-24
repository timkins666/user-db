FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache

COPY ./src/. ./src/

CMD ["/app/.venv/bin/fastapi", "run", "./src/userdb/main.py", "--port", "80"]

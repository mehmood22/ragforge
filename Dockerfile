FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    HF_HOME=/home/appuser/.cache/huggingface \
    PATH="/app/.venv/bin:$PATH"

# 1. Install dependencies
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# 2. Copy project files and install package
COPY README.md alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/
COPY evals/ ./evals/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

RUN mkdir -p /app/uploads /home/appuser/.cache/huggingface

EXPOSE 8000

CMD ["uvicorn", "ragforge.main:app", "--host", "0.0.0.0", "--port", "8000"]
FROM python:3.12-slim-bookworm

# Import the ultra-fast uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Prevent Python from writing .pyc files to disk and ensure clean logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project

# 👇 FIX: Added LICENSE* back to ensure the Python package builder doesn't crash
COPY src/ ./src/
COPY tests/ ./tests/
COPY README.md LICENSE* ./

# Final sync to link the project files
RUN uv sync --frozen

CMD ["python", "src/main.py"]
# Build desde la raiz del repo: docker build -f backend/Dockerfile backend/
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS build
WORKDIR /src

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Capa de dependencias separada del codigo: cambiar un .py no reinstala el mundo.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev


FROM python:3.13-slim-bookworm
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /src /app
ENV PATH="/app/.venv/bin:$PATH"

RUN chmod +x /app/entrypoint.sh \
    && useradd --create-home --uid 10001 app \
    && chown -R app:app /app
USER app

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]

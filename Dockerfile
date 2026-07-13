FROM node:22-bookworm-slim AS web
WORKDIR /build/apps/web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app
RUN apt-get update \
    && apt-get install --no-install-recommends -y git \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 agi
COPY --from=ghcr.io/astral-sh/uv:0.11.17 /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md alembic.ini ./
COPY apps/api/ ./apps/api/
RUN uv sync --frozen --no-dev --no-install-project && uv pip install --no-deps .
COPY --from=web /build/apps/web/dist ./apps/web/dist
COPY knowledge/ ./knowledge/
RUN mkdir -p /data/knowledge && chown -R agi:agi /app /data
USER agi
EXPOSE 8080
CMD ["uvicorn", "agi_server.main:app", "--host", "0.0.0.0", "--port", "8080"]

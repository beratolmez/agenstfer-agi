FROM node:22-bookworm-slim@sha256:53ada149d435c38b14476cb57e4a7da73c15595aba79bd6971b547ceb6d018bf AS web
WORKDIR /build/apps/web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app
RUN apt-get update \
    && apt-get install --no-install-recommends -y git \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 agi
COPY --from=ghcr.io/astral-sh/uv:0.11.17@sha256:03bdc89bb9798628846e60c3a9ad19006c8c3c724ccd2985a33145c039a0577b /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md alembic.ini ./
COPY apps/api/ ./apps/api/
COPY apps/services/ ./apps/services/
COPY mock_data/ ./mock_data/
RUN uv sync --frozen --no-dev --no-install-project && uv pip install --no-deps .
COPY --from=web /build/apps/web/dist ./apps/web/dist
RUN mkdir -p /data/knowledge && chown -R agi:agi /data
USER agi
EXPOSE 8080
CMD ["uvicorn", "agi_server.main:app", "--host", "0.0.0.0", "--port", "8080"]

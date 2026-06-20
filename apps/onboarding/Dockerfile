FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRUSTED_AGENTS_HOST=0.0.0.0 \
    TRUSTED_AGENTS_PORT=8088 \
    TRUSTED_AGENTS_DB=/data/onboarding.sqlite3

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data /app
USER appuser

EXPOSE 8088
CMD ["python", "-m", "trusted_agents_onboarding.app"]

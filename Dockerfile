FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
RUN uv sync --no-dev --no-install-project

COPY . /app
RUN uv sync --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# expose port
EXPOSE 8000

# create log dir
RUN mkdir -p /app/logs /app/uploads

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"

# If running behind a proxy like Nginx or Traefik add --proxy-headers
# "--forwarded-allow-ips *" to trust any IP addresses
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*", "--log-config", "uvicorn_log.json"]

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml .env ./
# uv.lock might not exist yet
RUN uv sync --no-dev

RUN apt-get update && apt-get install -y fonts-nanum && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["uv", "run", "python", "app.py"]

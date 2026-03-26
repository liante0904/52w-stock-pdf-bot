FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/

WORKDIR /app
COPY pyproject.toml uv.lock .env ./
RUN /uv/bin/uv sync --frozen --no-dev

RUN apt-get update && apt-get install -y fonts-nanum && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["/uv/bin/uv", "run", "python", "app.py"]

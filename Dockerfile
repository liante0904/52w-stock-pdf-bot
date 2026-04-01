# 1. Build stage
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev

# 2. Final stage
FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# 빌드 결과물 복사
COPY --from=builder /app/.venv /app/.venv
COPY . .

# 폰트 설치 (PDF 생성을 위해 필요)
RUN apt-get update && apt-get install -y fonts-nanum && rm -rf /var/lib/apt/lists/*

# 데이터 및 로그를 위한 마운트 포인트 생성
RUN mkdir -p /app/pdf /app/logs

# 각 서비스별 실행 명령어는 docker-compose.yml에서 설정함
CMD ["python", "app.py"]

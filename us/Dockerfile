FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/

WORKDIR /app
COPY pyproject.toml uv.lock .env ./
RUN /uv/bin/uv sync --frozen --no-dev

COPY . .
# fonts 폴더 복사 (존재할 경우)
RUN if [ -d "./fonts" ]; then cp -r ./fonts /usr/share/fonts/; fi

CMD ["/uv/bin/uv", "run", "python", "app.py"]

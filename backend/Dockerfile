FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 依存だけ先に入れてレイヤキャッシュを効かせる
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

COPY . .

EXPOSE 8000

# 起動: マイグレーション → seed(冪等) → uvicorn
CMD ["sh", "entrypoint.sh"]

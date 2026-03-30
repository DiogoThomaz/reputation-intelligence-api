# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps (sqlite is builtin)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# install python deps
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# copy source
COPY backend /app/backend

EXPOSE 8000

# Persist sqlite DB optionally by mounting a volume at /app/backend/app.db
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]

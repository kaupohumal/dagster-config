FROM python:3.14-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libgit2-dev \
        libssh2-1-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /venv \
 && /venv/bin/pip install --upgrade pip \
 && /venv/bin/pip install --no-cache-dir -r requirements.txt \
 && /venv/bin/pip install --no-cache-dir gunicorn


FROM python:3.14-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /venv /venv

COPY . .

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
 && chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

CMD ["sh", "-c", "gunicorn \
      --workers ${GUNICORN_WORKERS:-3} \
      --threads ${GUNICORN_THREADS:-2} \
      --worker-class gthread \
      --bind 0.0.0.0:5000 \
      --access-logfile - \
      --error-logfile - \
      --timeout 60 \
      app:app"]

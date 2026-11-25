FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ADA_MODE=cloud \
    PORT=8000

WORKDIR /app

COPY backend/requirements-cloud.txt ./backend/requirements-cloud.txt
RUN pip install --no-cache-dir -r backend/requirements-cloud.txt

COPY backend ./backend
RUN mkdir -p /app/workspace/reports /app/logs

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

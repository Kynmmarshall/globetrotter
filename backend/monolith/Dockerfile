FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app ./app
COPY data ./data
COPY static ./static

ENV MONOLITH_DATA_FILE=/app/data/db.json
ENV MONOLITH_SEED_DESTINATIONS_FILE=/app/data/destinations.json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

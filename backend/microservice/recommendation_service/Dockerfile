FROM python:3.12-slim

WORKDIR /srv/app

COPY pyproject.toml ./
COPY app ./app
COPY static ./static

RUN pip install --no-cache-dir .

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

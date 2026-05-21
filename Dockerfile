FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN DJANGO_SECRET_KEY=collectstatic python manage.py collectstatic --noinput

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --system --no-create-home appuser
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2}"]

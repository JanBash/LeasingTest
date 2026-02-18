#!/bin/sh

# Применяем миграции
python manage.py migrate --noinput

# Пытаемся создать суперпользователя (если он уже есть, команда просто пропустит шаг)
python manage.py createsuperuser --noinput || true

# Запускаем сервер
gunicorn core.wsgi:application --bind 0.0.0.0:8000
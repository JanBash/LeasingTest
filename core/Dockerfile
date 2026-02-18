# Используем Python 3.12
FROM python:3.12-slim

# Исправляем имена пакетов для Debian Bookworm/Trixie
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Настройка рабочей папки
WORKDIR /app

# Сначала копируем зависимости, чтобы кэшировать этот слой
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Собираем статику
# Используем заглушку для SECRET_KEY
RUN SECRET_KEY=build_secret python manage.py collectstatic --noinput

# Запуск
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
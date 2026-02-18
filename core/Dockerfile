# Используем официальный легкий образ Python 3.12
FROM python:3.12-slim

# 1. Устанавливаем системные библиотеки для WeasyPrint и базы данных
# Мы используем apt-get (как в Ubuntu), это надежнее, чем Nixpacks
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libglib2.0-0 \
    python3-cffi \
    python3-brotli \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Настраиваем рабочую папку
WORKDIR /app

# 3. Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем весь код проекта
COPY . .

# 5. Собираем статику (CSS/JS)
# Используем заглушку для SECRET_KEY, так как при сборке он не важен
RUN SECRET_KEY=build_secret python manage.py collectstatic --noinput

# 6. Команда запуска сервера (Gunicorn)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
# Используем Python 3.12
FROM python:3.12-slim

# Устанавливаем системные библиотеки + компилятор для сборки pycairo
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Настройка рабочей папки
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Даем права на выполнение скрипта
RUN chmod +x entrypoint.sh

# Собираем статику
RUN SECRET_KEY=build_secret python manage.py collectstatic --noinput

# Запускаем через entrypoint
CMD ["./entrypoint.sh"]

# Запуск через Gunicorn
# Важно: убедитесь, что путь core.wsgi верный (папка с wsgi.py называется core)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]


# Используем официальный Python-образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Открываем нужный порт
EXPOSE 8080

# Запускаем приложение
CMD ["python", "main.py"]

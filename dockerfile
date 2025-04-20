# Dockerfile
FROM python:3.11

# 1. Set workdir
WORKDIR /app

# 2. Install system deps (if any) then Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy code
COPY . .

# 4. Expose port and set default command
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
CMD ["gunicorn", "social_media.wsgi:application", "--bind", "0.0.0.0:8000"]

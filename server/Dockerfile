# server/Dockerfile
FROM python:3.12-slim

# Evitar buffering en logs
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y luego instalar
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar el resto del código del backend
COPY . /app

# Exponer puerto de FastAPI
EXPOSE 8000

# Comando por defecto: levantar FastAPI con uvicorn
# Ajusta "main:app" si tu archivo o variable de app se llaman distinto
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
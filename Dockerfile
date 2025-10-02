FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Instalación del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libopenjp2-7 \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    poppler-utils \
    tesseract-ocr \
    python3-dev \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copia de archivos del proyecto
COPY . .

# Instalación de dependencias Python
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copiar crontab
COPY scripts/crontab /etc/cron.d/siss-cron

# Dar permisos correctos y registrar el cronjob
RUN chmod 0644 /etc/cron.d/siss-cron && \
    crontab /etc/cron.d/siss-cron

# Crear archivo de log
RUN touch /var/log/cron.log

# Ejecutar cron en foreground (para mantener el contenedor activo)
CMD ["cron", "-f"]

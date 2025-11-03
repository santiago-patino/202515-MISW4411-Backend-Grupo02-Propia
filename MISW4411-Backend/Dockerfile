# =========================================================================
# STAGE 1: Build - Instala dependencias en un entorno completo
# =========================================================================
FROM python:3.10-slim AS builder

# --- Configuración del entorno ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia solo el archivo de requerimientos para aprovechar el cache de Docker
COPY requirements.txt .

# Actualizamos pip y herramientas de compilación
RUN python -m pip install --upgrade pip setuptools wheel

# Instala las dependencias en una ubicación que será copiada a la etapa final
# Usa cache de pip cuando sea posible
RUN pip wheel --wheel-dir /app/wheels -r requirements.txt || \
    (echo "Primer intento fallido, reintentando..." && sleep 5 && \
     pip wheel --wheel-dir /app/wheels -r requirements.txt)


# =========================================================================
# STAGE 2: Final - Crea la imagen de producción ligera y segura
# =========================================================================
FROM python:3.10-slim

# --- Configuración del entorno y usuario no-root ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar solo dependencias del sistema necesarias para producción
# poppler-utils es requerido para procesar PDFs con markitdown
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Crea un directorio de trabajo y un usuario no-root para ejecutar la aplicación
WORKDIR /app
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

# --- Copia de artefactos ---
# Copia las dependencias pre-compiladas de la etapa de build
COPY --from=builder /app/wheels /wheels/
COPY --from=builder /app/requirements.txt .

# Instala las dependencias desde los wheels locales (más rápido que descargar)
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copia el código fuente de la aplicación
COPY ./app ./app
COPY main.py .
COPY apikey.json .

# Asigna la propiedad del directorio de trabajo al usuario no-root
RUN chown -R appuser:appgroup /app

# Cambia al usuario no-root para la ejecución
USER appuser

# --- Configuración de red y ejecución ---
# Expone el puerto en el que corre la aplicación
EXPOSE 8000

# Comando para iniciar el servidor de producción
# Uvicorn es iniciado para escuchar en todas las interfaces de red
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

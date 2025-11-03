# =========================================================================
# STAGE 1: Build - Instala dependencias en un entorno completo
# =========================================================================
FROM python:3.10-slim AS builder

# --- Configuración del entorno ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# --- Instalación de dependencias ---
# Copia solo el archivo de requerimientos para aprovechar el cache de Docker
COPY requirements.txt .

# Instala las dependencias en una ubicación que será copiada a la etapa final
# Se implementa un reintento para mitigar problemas de red con paquetes grandes
RUN for i in 1 2 3; do \
        pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt && break || \
        echo "Intento $i fallido, reintentando en 5 segundos..." && sleep 5; \
    done


# =========================================================================
# STAGE 2: Final - Crea la imagen de producción ligera y segura
# =========================================================================
FROM python:3.10-slim

# --- Configuración del entorno y usuario no-root ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias para markitdown[pdf]
# poppler-utils es requerido para procesar PDFs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Crea un directorio de trabajo y un usuario no-root para ejecutar la aplicación
WORKDIR /app
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

# --- Copia de artefactos ---
# Copia las dependencias pre-compiladas de la etapa de build
COPY --from=builder /app/wheels /wheels/
COPY --from=builder /app/requirements.txt .

# Instala las dependencias desde los wheels locales sin necesidad de compilación
RUN pip install --no-cache-dir /wheels/*

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

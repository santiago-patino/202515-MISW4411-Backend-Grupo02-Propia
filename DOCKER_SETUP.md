# Configuración Docker para MISW4411

Este documento describe cómo configurar y ejecutar todos los servicios usando Docker Compose.

## Estructura de Servicios

- **agent-backend**: Puerto 8000 (Backend de agentes inteligentes)
- **backend**: Puerto 8001 (Backend RAG principal)
- **frontend**: Puerto 3000 (Frontend React/Vite)

## Requisitos Previos

1. Docker y Docker Compose instalados
2. API Key de Google configurada

## Configuración Inicial

### 1. Crear archivo .env

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
# API Key de Google (requerida para ambos backends)
GOOGLE_API_KEY=tu_api_key_aqui

# URL del backend para el frontend
# Para desarrollo local:
VITE_BACKEND_URL=http://localhost:8000

# Para producción en GCP (reemplazar con la IP externa de tu VM):
# VITE_BACKEND_URL=http://TU_IP_EXTERNA:8000
```

### 2. Para VM de GCP

Si vas a ejecutar en una VM de GCP:

1. Obtén la IP externa de tu VM:
   ```bash
   gcloud compute instances describe NOMBRE_DE_TU_VM --zone=ZONA --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
   ```

2. Actualiza el archivo `.env`:
   ```env
   VITE_BACKEND_URL=http://TU_IP_EXTERNA:8000
   ```

3. Asegúrate de que los puertos 3000, 8000 y 8001 estén abiertos en el firewall de GCP:
   ```bash
   gcloud compute firewall-rules create allow-docker-ports \
     --allow tcp:3000,tcp:8000,tcp:8001 \
     --source-ranges 0.0.0.0/0 \
     --description "Allow Docker services ports"
   ```

## Ejecución

### Construir y ejecutar todos los servicios

```bash
docker-compose up --build
```

### Ejecutar en segundo plano

```bash
docker-compose up -d --build
```

### Ver logs

```bash
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f agent-backend
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Detener servicios

```bash
docker-compose down
```

### Reconstruir un servicio específico

```bash
docker-compose up --build agent-backend
```

## Acceso a los Servicios

Una vez que los servicios estén ejecutándose:

- **Frontend**: http://localhost:3000 (o http://TU_IP_EXTERNA:3000 en GCP)
- **Agent Backend API**: http://localhost:8000 (o http://TU_IP_EXTERNA:8000 en GCP)
- **Backend RAG API**: http://localhost:8001 (o http://TU_IP_EXTERNA:8001 en GCP)

## Volúmenes Persistentes

Los siguientes directorios se mantienen fuera de los contenedores:

- `./MISW4411-Backend/docs`: Documentos descargados
- `./MISW4411-Backend/logs`: Logs de procesamiento
- `./MISW4411-Backend/chroma_db`: Base de datos vectorial ChromaDB
- `./MISW4411-Backend/.cache`: Cache de modelos de HuggingFace

## Solución de Problemas

### El frontend no se conecta al backend

1. Verifica que `VITE_BACKEND_URL` en `.env` esté configurada correctamente
2. Para GCP, asegúrate de usar la IP externa, no `localhost`
3. Reconstruye el frontend después de cambiar `VITE_BACKEND_URL`:
   ```bash
   docker-compose up --build frontend
   ```

### Error de CORS

Si ves errores de CORS, verifica que los orígenes permitidos en los archivos `main.py` de ambos backends incluyan la URL desde la que accedes al frontend.

### Los servicios no inician

1. Verifica que los puertos 3000, 8000 y 8001 no estén en uso:
   ```bash
   # Linux/Mac
   lsof -i :3000 -i :8000 -i :8001
   
   # Windows
   netstat -ano | findstr :3000
   netstat -ano | findstr :8000
   netstat -ano | findstr :8001
   ```

2. Verifica los logs:
   ```bash
   docker-compose logs
   ```

## Comandos Útiles

```bash
# Ver estado de los contenedores
docker-compose ps

# Reiniciar un servicio específico
docker-compose restart agent-backend

# Ejecutar comandos dentro de un contenedor
docker-compose exec agent-backend bash
docker-compose exec backend bash
docker-compose exec frontend sh

# Limpiar todo (contenedores, imágenes, volúmenes)
docker-compose down -v --rmi all
```


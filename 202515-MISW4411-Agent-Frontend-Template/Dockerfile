# =========================================================================
# STAGE 1: Build - Compila la aplicación React/Vite
# =========================================================================
FROM node:18-alpine AS builder

WORKDIR /app

# Argumento de build para la URL del backend
ARG VITE_BACKEND_URL=http://localhost:8000

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm ci

# Copiar el código fuente
COPY . .

# Construir la aplicación para producción con la variable de entorno
RUN VITE_BACKEND_URL=${VITE_BACKEND_URL} npm run build

# =========================================================================
# STAGE 2: Production - Servir la aplicación con nginx
# =========================================================================
FROM nginx:alpine

# Copiar los archivos construidos desde el stage de build
COPY --from=builder /app/dist /usr/share/nginx/html

# Crear configuración de nginx para el puerto 3000
RUN echo 'server { \
    listen 3000; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # Configuración para SPA (Single Page Application) \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # Cache para assets estáticos \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
    \
    # Headers de seguridad \
    add_header X-Frame-Options "SAMEORIGIN" always; \
    add_header X-Content-Type-Options "nosniff" always; \
    add_header X-XSS-Protection "1; mode=block" always; \
}' > /etc/nginx/conf.d/default.conf

# Exponer el puerto 3000
EXPOSE 3000

# Iniciar nginx
CMD ["nginx", "-g", "daemon off;"]


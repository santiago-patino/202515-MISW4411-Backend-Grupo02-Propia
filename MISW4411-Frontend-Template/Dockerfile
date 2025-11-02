# Etapa de Build
FROM node:18-alpine AS builder

WORKDIR /app

# Copia package.json y package-lock.json para instalar dependencias
COPY package*.json ./

# Instala dependencias
RUN npm install --production=false

# Copia el resto del código fuente
COPY . .

# Compila la aplicación
RUN npm run build

# Etapa Final
FROM node:18-alpine AS runner

WORKDIR /app

# Crea un usuario no-root
RUN addgroup --system --gid 1001 appuser
RUN adduser --system --uid 1001 appuser

# Copia solo los artefactos de la etapa de build
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/index.html ./index.html
COPY --from=builder /app/public ./public

# Establece el usuario no-root
USER appuser

# Expone el puerto que la aplicación utiliza
EXPOSE 3000

# Comando para iniciar la aplicación
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]

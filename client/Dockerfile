# client/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copiar archivos de definición de dependencias
COPY package.json package-lock.json ./

# Instalar dependencias (usa package-lock con npm ci)
RUN npm ci

# Copiar el resto del código del frontend
COPY . /app

# Exponer puerto default de Vite
EXPOSE 5173

# Comando para levantar Vite en modo dev dentro del contenedor
# --host 0.0.0.0 para que sea accesible desde fuera del contenedor
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# Stage 1: Build Stage
FROM node:20-alpine AS build-stage

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source and build the app
COPY . .
# Vite creates a 'dist' folder by default
RUN npm run build

FROM nginx:stable-alpine AS production-stage

COPY --from=build-stage /app/dist /usr/share/nginx/html

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]
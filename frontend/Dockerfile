FROM node:22-slim

WORKDIR /app

# Fijamos la misma versión de pnpm que usas en local para evitar
# conflictos de política entre el lockfile y el gestor de paquetes
RUN npm install -g pnpm@10.15.1

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 5173

CMD ["pnpm", "dev", "--host"]

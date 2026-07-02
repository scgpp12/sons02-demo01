# 開発用（docker-compose）: Vite dev server をそのまま動かす
FROM node:22-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]

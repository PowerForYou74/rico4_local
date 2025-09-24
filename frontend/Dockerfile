FROM node:20-slim AS deps
WORKDIR /app
ENV CI=true \
NEXT_TELEMETRY_DISABLED=1
COPY package*.json ./
RUN npm ci --ignore-scripts

FROM node:20-slim AS builder
WORKDIR /app
ENV CI=true \
NEXT_TELEMETRY_DISABLED=1 \
NODE_ENV=production
COPY package*.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production \
NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/out ./out
EXPOSE 3000
CMD ["npx", "serve", "out", "-s", "-l", "3000"]
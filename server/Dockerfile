# syntax=docker/dockerfile:1
# Build từ GỐC repo:  docker build -f server/Dockerfile -t b1-api .
FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY server/package.json server/package-lock.json ./
RUN npm ci --omit=dev

FROM node:22-bookworm-slim
ENV NODE_ENV=production \
    CONTENT_DIR=/app/content
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY server/package.json ./
COPY server/src ./src
COPY server/scripts ./scripts
COPY server/migrations ./migrations
COPY web/public/data ./content
USER node
EXPOSE 3000
CMD ["node", "src/index.js"]

# ── Build stage ───────────────────────────────────────────
# Node 22: Vite 7 requires ^20.19.0 || >=22.12.0 and react-router 7
# requires >=20. The previous node:18-alpine base could not build them.
FROM node:22-alpine AS builder
WORKDIR /app

# Install from the lockfile so image builds are reproducible.
COPY package.json package-lock.json ./
RUN npm ci

# Vite inlines env vars at build time, so the API URL must be declared
# as a build arg here — docker-compose passes it, but without this ARG
# the value was silently discarded and the build fell back to localhost.
ARG VITE_API_URL=http://localhost:8000/api
ENV VITE_API_URL=$VITE_API_URL

COPY . .
RUN npm run build

# ── Serve stage ───────────────────────────────────────────
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# syntax=docker/dockerfile:1.7
# -----------------------------------------------------------------------------
# Frontend Dockerfile - two-stage build.
#
# Stage 1 (build): runs `npm install` and `vite build` to produce the static
#   bundle in /app/dist.
# Stage 2 (serve): nginx-alpine, with the static bundle copied in and our
#   custom nginx.conf for SPA routing + /api proxying.
# -----------------------------------------------------------------------------

# --- Stage 1: build ---------------------------------------------------------
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files first for better layer caching - npm install only re-runs
# when package.json/lock changes, not on every source edit.
COPY package*.json ./
RUN npm install

# Copy source and build the static bundle.
COPY . .
RUN npm run build

# --- Stage 2: serve ---------------------------------------------------------
FROM nginx:1.27-alpine AS serve

# Default to the in-cluster service DNS name. Overridable at deploy time
# via env so the same image works in different environments.
ENV BACKEND_URL=http://backend:8000

# Copy our nginx config as a template - it has ${BACKEND_URL} that gets
# substituted at container start.
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy the built static assets from the build stage.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# The default nginx:alpine entrypoint already runs envsubst on files in
# /etc/nginx/templates/, so $BACKEND_URL gets injected automatically.
CMD ["nginx", "-g", "daemon off;"]
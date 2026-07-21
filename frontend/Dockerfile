# ─── Frontend Dockerfile (multi-stage) ───────────────────────────────────────
# Stage 1 — Build the React + Vite application
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies (copy lockfile first for better layer caching)
COPY package.json package-lock.json ./
RUN npm ci --silent

# Copy the rest of the frontend source and build
COPY . .
RUN npm run build

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Serve with Nginx
# ─────────────────────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine

# Remove default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Copy the Vite production build from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# Multi-stage build: compile the React dashboard, then serve it from the FastAPI app.
# One image, one process — fits Railway's persistent-WebSocket model for the voice relay.

# ---- stage 1: build the dashboard ----
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
# vite is configured to output to ../backend/static; redirect it here instead.
RUN npm run build -- --outDir /web/dist --emptyOutDir

# ---- stage 2: python backend ----
FROM python:3.11-slim AS app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
# bring in the compiled dashboard
COPY --from=web /web/dist ./static
# seed the knowledge base into the image's data dir at build time is skipped;
# the app seeds lazily/at first run via /api/seed-on-start (lifespan ensures baseline).
EXPOSE 8000
CMD ["sh", "-c", "python -m app.seed || true; uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

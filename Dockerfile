# Production image: one container builds the Mini App, then serves the API +
# static frontend and runs the Telegram bot in a single process (RUN_BOT=1).
# Works on any Docker host (Render, Fly, a VPS). Render/HF set $PORT.

# ---- stage 1: build the Mini App ----
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- stage 2: python runtime ----
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY gararide/ ./gararide/
COPY seed/ ./seed/
COPY --from=web /web/dist ./frontend/dist

# Run the bot poller alongside the API, like the old single-process demo.
ENV RUN_BOT=1
CMD ["sh", "-c", "uvicorn gararide.server:app --host 0.0.0.0 --port ${PORT:-8000}"]

FROM node:22-bookworm-slim AS frontend
WORKDIR /app
RUN npm install -g pnpm@11.25.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY index.html tsconfig.json vite.config.ts ./
COPY frontend ./frontend
RUN pnpm build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY backend ./backend
COPY --from=frontend /app/dist ./dist
RUN useradd --create-home --uid 10001 appuser && mkdir -p /app/data && chown appuser:appuser /app/data
USER appuser
ENV PYTHONPATH=/app/backend
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "supportlens.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

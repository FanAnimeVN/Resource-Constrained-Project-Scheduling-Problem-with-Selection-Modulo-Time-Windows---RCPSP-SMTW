# Một image phục vụ cả REST API và giao diện web tại cổng 8000.
FROM node:22-slim AS web
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/ backend/
RUN pip install --no-cache-dir ./backend
COPY data/ data/
COPY --from=web /app/frontend/dist frontend/dist
ENV CPLAN_DATA_DIR=/app/data \
    CPLAN_WEB_DIST=/app/frontend/dist
EXPOSE 8000
CMD ["uvicorn", "curriculum_planner.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

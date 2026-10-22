# Lệnh tiện ích. Chạy `make help` để xem danh sách.
PY := backend/.venv/bin
DATASET ?= hcmus_cntt_k2020

.PHONY: help setup setup-backend setup-frontend lint test test-backend test-frontend e2e \
        dev-api dev-web build serve validate-data gen-api demo

help:
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

setup: setup-backend setup-frontend ## Cài đặt toàn bộ phụ thuộc

setup-backend: ## Tạo venv và cài backend (ưu tiên uv, fallback pip)
	cd backend && (command -v uv >/dev/null && uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]") \
	  || (python3 -m venv .venv && .venv/bin/pip install -e ".[dev]")

setup-frontend: ## Cài gói npm cho giao diện
	cd frontend && npm ci

lint: ## Kiểm tra style backend + kiểu TypeScript
	$(PY)/ruff check backend/src backend/tests
	$(PY)/ruff format --check backend/src backend/tests
	cd frontend && npm run typecheck

test: test-backend test-frontend ## Chạy toàn bộ kiểm thử (trừ e2e)

test-backend: ## pytest: unit, property, BDD AC-01..AC-07, API
	cd backend && .venv/bin/python -m pytest

test-frontend: ## vitest
	cd frontend && npm test

e2e: ## Playwright smoke test (tự build và khởi động server)
	cd frontend && npx playwright test

validate-data: ## Kiểm tra dữ liệu CTĐT
	$(PY)/cplan validate $(DATASET)

dev-api: ## Chạy API ở chế độ phát triển (cổng 8000)
	cd backend && .venv/bin/uvicorn curriculum_planner.api.app:app --reload --port 8000

dev-web: ## Chạy giao diện ở chế độ phát triển (cổng 5173, proxy /api → 8000)
	cd frontend && npm run dev

build: ## Build giao diện vào frontend/dist
	cd frontend && npm run build

serve: build ## Một tiến trình phục vụ cả API và giao diện tại http://localhost:8000
	cd backend && .venv/bin/uvicorn curriculum_planner.api.app:app --port 8000

gen-api: ## Sinh lại kiểu TypeScript từ OpenAPI của backend
	cd frontend && npm run gen:api

demo: ## In lộ trình mẫu ra terminal
	$(PY)/cplan plan --student sv02 --strategy BALANCED --no-explain
	$(PY)/cplan plan --student sv04

.PHONY: all backend frontend install clean stop help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Python virtual environment
VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Default target - runs in foreground, stops with Ctrl+C
all:
	@echo "$(BLUE)Starting AI Terminal...$(NC)"
	@echo "$(GREEN)Backend: http://localhost:8001$(NC)"
	@echo "$(GREEN)Frontend: http://localhost:5174$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop all services$(NC)"
	@echo ""
	@trap 'make stop' INT; \
	(cd backend && ../$(PYTHON) -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload) & \
	BACKEND_PID=$$!; \
	sleep 3; \
	(cd frontend && npm start) & \
	FRONTEND_PID=$$!; \
	wait

# Install all dependencies
install:
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@echo "$(YELLOW)Setting up Python virtual environment...$(NC)"
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	@echo "$(YELLOW)Installing Node.js dependencies...$(NC)"
	cd frontend && npm install
	@echo "$(GREEN)✓ Installation complete!$(NC)"

# Start backend server only
backend:
	@echo "$(BLUE)Starting backend server...$(NC)"
	@cd backend && ../$(PYTHON) -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload

# Start frontend with Electron only
frontend:
	@echo "$(BLUE)Starting frontend with Electron...$(NC)"
	@cd frontend && npm start

# Stop all running processes
stop:
	@echo "$(YELLOW)Stopping backend and frontend...$(NC)"
	@pkill -f "uvicorn app:app" || true
	@pkill -f "vite" || true
	@pkill -f "electron" || true
	@echo "$(GREEN)✓ All processes stopped$(NC)"

# Clean build artifacts and caches
clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf frontend/dist 2>/dev/null || true
	@rm -rf frontend/node_modules/.vite 2>/dev/null || true
	@echo "$(GREEN)✓ Clean complete$(NC)"

# Docker commands
docker-build:
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker compose build
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-up:
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✓ Docker containers running$(NC)"
	@echo "$(GREEN)  Backend: http://localhost:8001$(NC)"
	@echo "$(GREEN)  Frontend: http://localhost$(NC)"

docker-down:
	@echo "$(YELLOW)Stopping Docker containers...$(NC)"
	docker compose down
	@echo "$(GREEN)✓ Docker containers stopped$(NC)"

docker-logs:
	@docker compose logs -f

# Development helpers
dev: all
	@echo "$(GREEN)✓ Development environment running!$(NC)"
	@echo "$(BLUE)  Backend: http://localhost:8001$(NC)"
	@echo "$(BLUE)  Frontend: http://localhost:5174$(NC)"
	@echo "$(BLUE)  API Docs: http://localhost:8001/docs$(NC)"

# Show help
help:
	@echo "$(BLUE)AI Terminal - Available Commands:$(NC)"
	@echo ""
	@echo "$(GREEN)make all$(NC)          - Start backend and frontend (Electron)"
	@echo "$(GREEN)make install$(NC)      - Install all dependencies"
	@echo "$(GREEN)make backend$(NC)      - Start backend server only"
	@echo "$(GREEN)make frontend$(NC)     - Start frontend with Electron only"
	@echo "$(GREEN)make stop$(NC)         - Stop all running processes"
	@echo "$(GREEN)make clean$(NC)        - Clean build artifacts and caches"
	@echo "$(GREEN)make dev$(NC)          - Start development environment"
	@echo ""
	@echo "$(YELLOW)Docker Commands:$(NC)"
	@echo "$(GREEN)make docker-build$(NC) - Build Docker images"
	@echo "$(GREEN)make docker-up$(NC)    - Start Docker containers"
	@echo "$(GREEN)make docker-down$(NC)  - Stop Docker containers"
	@echo "$(GREEN)make docker-logs$(NC)  - View Docker logs"
	@echo ""
	@echo "$(BLUE)Quick Start:$(NC)"
	@echo "  1. $(GREEN)make install$(NC)  - First time setup"
	@echo "  2. $(GREEN)make all$(NC)      - Start the application"
	@echo "  3. $(GREEN)make stop$(NC)     - Stop when done"

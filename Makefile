.PHONY: help install install-dev setup clean format lint type-check security test test-cov pre-commit check
.PHONY: ingest ingest-dry-run rag rag-question update lock shell zip zip-manual
.PHONY: docker-help docker-build docker-up docker-up-nginx docker-down docker-restart docker-logs docker-shell
.PHONY: docker-test docker-ingest docker-clean docker-rebuild docker-dev docker-format docker-lint
.PHONY: docker-status docker-stats docker-backup docker-restore

# Default target
help:  ## Show this help message
	@echo "Shokobot - Available commands:"
	@echo ""
	@echo "Local Development:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -v "^docker-" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Docker Commands:"
	@grep -E '^docker-[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Local Development Commands
# ============================================================================

install:  ## Install production dependencies
	poetry install --only main

install-dev:  ## Install all dependencies including dev tools
	poetry install --with dev
	poetry run pre-commit install

setup:  ## Run initial setup script
	./setup.sh

clean:  ## Clean up generated files
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

format:  ## Format code with ruff
	poetry run ruff format .

lint:  ## Lint code with ruff
	poetry run ruff check . --fix

type-check:  ## Run type checking with mypy
	poetry run mypy .

security:  ## Run security checks with bandit
	poetry run bandit -r services models utils

test:  ## Run tests
	poetry run pytest

test-cov:  ## Run tests with coverage report
	poetry run pytest --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

pre-commit:  ## Run all pre-commit hooks
	poetry run pre-commit run --all-files

check: format lint type-check security test  ## Run all quality checks

ingest:  ## Run ingestion process
	poetry run shokobot ingest

ingest-dry-run:  ## Validate data without ingesting (dry-run)
	poetry run shokobot ingest --dry-run

rag:  ## Start interactive RAG REPL
	poetry run shokobot repl

rag-question:  ## Ask a single question (use Q="your question")
	poetry run shokobot query -q "$(Q)"

update:  ## Update dependencies
	poetry update

lock:  ## Update lock file without installing
	poetry lock --no-update

shell:  ## Start poetry shell
	poetry shell

zip:  ## Create a zipfile of all tracked files (excluding .gitignore entries)
	@echo "Creating archive..."
	@PROJECT_NAME=$$(basename $$(pwd)); \
	TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	ZIP_NAME="$${PROJECT_NAME}_$${TIMESTAMP}.zip"; \
	git archive -o "$${ZIP_NAME}" HEAD && \
	echo "Archive created: $${ZIP_NAME}" || \
	(echo "Error: Not a git repository or git archive failed. Use 'make zip-manual' instead." && exit 1)

zip-manual:  ## Create a zipfile manually (for non-git projects)
	@echo "Creating archive manually..."
	@PROJECT_NAME=$$(basename $$(pwd)); \
	TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	ZIP_NAME="$${PROJECT_NAME}_$${TIMESTAMP}.zip"; \
	zip -r "$${ZIP_NAME}" . -x@.gitignore -x "*.zip" -x ".git/*" && \
	echo "Archive created: $${ZIP_NAME}"

# ============================================================================
# Docker Commands
# ============================================================================

docker-help:  ## Show Docker-specific help
	@echo "ShokoBot Docker Commands"
	@echo "========================"
	@echo "make docker-build       - Build Docker image"
	@echo "make docker-up          - Start services"
	@echo "make docker-down        - Stop services"
	@echo "make docker-restart     - Restart services"
	@echo "make docker-logs        - View logs"
	@echo "make docker-shell       - Open shell in container"
	@echo "make docker-test        - Run tests in container"
	@echo "make docker-ingest      - Run data ingestion"
	@echo "make docker-clean       - Remove containers and volumes"
	@echo "make docker-rebuild     - Rebuild and restart"
	@echo ""
	@echo "With Nginx:"
	@echo "make docker-up-nginx    - Start with nginx reverse proxy"
	@echo ""
	@echo "Development:"
	@echo "make docker-dev         - Start in development mode (requires docker-compose.override.yml)"
	@echo "make docker-format      - Format code"
	@echo "make docker-lint        - Run linters"

docker-build:  ## Build Docker image
	docker-compose build

docker-up:  ## Start Docker services
	docker-compose up -d
	@echo "ShokoBot is running at http://localhost:7860"

docker-up-nginx:  ## Start with nginx reverse proxy
	docker-compose --profile with-nginx up -d
	@echo "ShokoBot is running at http://localhost"

docker-down:  ## Stop Docker services
	docker-compose down

docker-restart: docker-down docker-up  ## Restart Docker services

docker-logs:  ## View Docker logs
	docker-compose logs -f shokobot

docker-shell:  ## Open shell in Docker container
	docker-compose exec shokobot bash

docker-test:  ## Run tests in Docker container
	docker-compose exec shokobot pytest

docker-ingest:  ## Run data ingestion in Docker
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make docker-ingest FILE=input/shoko_tvshows.json"; \
		exit 1; \
	fi
	docker-compose exec shokobot shokobot ingest $(FILE)

docker-clean:  ## Remove Docker containers and volumes
	docker-compose down -v
	docker system prune -f

docker-rebuild: docker-clean docker-build docker-up  ## Rebuild and restart Docker

docker-dev:  ## Start in development mode (with hot reload)
	@if [ ! -f docker-compose.override.yml ]; then \
		echo "Error: docker-compose.override.yml not found"; \
		echo "Create it from the example:"; \
		echo "  cp docker-compose.override.yml.example docker-compose.override.yml"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up

docker-format:  ## Format code in Docker container
	docker-compose exec shokobot ruff format .

docker-lint:  ## Run linters in Docker container
	docker-compose exec shokobot ruff check .
	docker-compose exec shokobot mypy services models utils prompts ui

docker-status:  ## Show Docker container status
	docker-compose ps

docker-stats:  ## Show Docker resource usage
	docker stats shokobot --no-stream

docker-backup:  ## Backup Docker volumes
	@mkdir -p backups
	@echo "Backing up ChromaDB..."
	@VOLUME_NAME=$$(docker volume ls --format '{{.Name}}' | grep chroma_data | head -n1); \
	if [ -z "$$VOLUME_NAME" ]; then \
		echo "Error: ChromaDB volume not found. Run 'docker volume ls' to see available volumes."; \
		exit 1; \
	fi; \
	echo "Backing up volume: $$VOLUME_NAME"; \
	docker run --rm -v $$VOLUME_NAME:/data -v $(PWD)/backups:/backup \
		alpine tar czf /backup/chroma_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .
	@echo "Backup complete!"

docker-restore:  ## Restore Docker volumes
	@if [ -z "$(BACKUP)" ]; then \
		echo "Usage: make docker-restore BACKUP=backups/chroma_20240101_120000.tar.gz"; \
		exit 1; \
	fi
	@echo "Restoring from $(BACKUP)..."
	@VOLUME_NAME=$$(docker volume ls --format '{{.Name}}' | grep chroma_data | head -n1); \
	if [ -z "$$VOLUME_NAME" ]; then \
		echo "Error: ChromaDB volume not found. Run 'docker volume ls' to see available volumes."; \
		exit 1; \
	fi; \
	echo "Restoring to volume: $$VOLUME_NAME"; \
	docker run --rm -v $$VOLUME_NAME:/data -v $(PWD)/backups:/backup \
		alpine tar xzf /backup/$(notdir $(BACKUP)) -C /data
	@echo "Restore complete!"

.PHONY: help build up down logs shell test clean ingest

# Default target
help:
	@echo "ShokoBot Docker Commands"
	@echo "========================"
	@echo "make build       - Build Docker image"
	@echo "make up          - Start services"
	@echo "make down        - Stop services"
	@echo "make restart     - Restart services"
	@echo "make logs        - View logs"
	@echo "make shell       - Open shell in container"
	@echo "make test        - Run tests in container"
	@echo "make ingest      - Run data ingestion"
	@echo "make clean       - Remove containers and volumes"
	@echo "make rebuild     - Rebuild and restart"
	@echo ""
	@echo "With Nginx:"
	@echo "make up-nginx    - Start with nginx reverse proxy"
	@echo ""
	@echo "Development:"
	@echo "make dev         - Start in development mode"
	@echo "make format      - Format code"
	@echo "make lint        - Run linters"

# Build Docker image
build:
	docker-compose build

# Start services
up:
	docker-compose up -d
	@echo "ShokoBot is running at http://localhost:7860"

# Start with nginx
up-nginx:
	docker-compose --profile with-nginx up -d
	@echo "ShokoBot is running at http://localhost"

# Stop services
down:
	docker-compose down

# Restart services
restart: down up

# View logs
logs:
	docker-compose logs -f shokobot

# Open shell in container
shell:
	docker-compose exec shokobot bash

# Run tests
test:
	docker-compose exec shokobot pytest

# Run data ingestion
ingest:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make ingest FILE=data/anime.json"; \
		exit 1; \
	fi
	docker-compose exec shokobot python -m cli.main ingest $(FILE)

# Clean up
clean:
	docker-compose down -v
	docker system prune -f

# Rebuild and restart
rebuild: clean build up

# Development mode (with hot reload)
dev:
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up

# Format code
format:
	docker-compose exec shokobot ruff format .

# Run linters
lint:
	docker-compose exec shokobot ruff check .
	docker-compose exec shokobot mypy services models utils prompts ui

# Show container status
status:
	docker-compose ps

# Show resource usage
stats:
	docker stats shokobot --no-stream

# Backup volumes
backup:
	@mkdir -p backups
	@echo "Backing up ChromaDB..."
	@docker run --rm -v shokobot_chroma_data:/data -v $(PWD)/backups:/backup \
		alpine tar czf /backup/chroma_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .
	@echo "Backup complete!"

# Restore volumes
restore:
	@if [ -z "$(BACKUP)" ]; then \
		echo "Usage: make restore BACKUP=backups/chroma_20240101_120000.tar.gz"; \
		exit 1; \
	fi
	@echo "Restoring from $(BACKUP)..."
	@docker run --rm -v shokobot_chroma_data:/data -v $(PWD)/backups:/backup \
		alpine tar xzf /backup/$(notdir $(BACKUP)) -C /data
	@echo "Restore complete!"

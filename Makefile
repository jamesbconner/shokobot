.PHONY: help install install-dev clean format lint type-check security test test-cov ingest rag setup

help:  ## Show this help message
	@echo "Shokobot - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

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
	poetry run shokobot-rag --repl

rag-question:  ## Ask a single question (use Q="your question")
	poetry run shokobot-rag -q "$(Q)"

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

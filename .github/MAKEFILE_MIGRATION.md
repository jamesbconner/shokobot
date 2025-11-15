# Makefile Command Migration Guide

## Overview

The Makefile has been reorganized to support both local development and Docker-based workflows. All Docker commands now have a `docker-` prefix to avoid conflicts with local development commands.

## Command Mapping

### Docker Commands (New Prefix)

| Old Command | New Command | Description |
|------------|-------------|-------------|
| `make build` | `make docker-build` | Build Docker image |
| `make up` | `make docker-up` | Start Docker services |
| `make down` | `make docker-down` | Stop Docker services |
| `make restart` | `make docker-restart` | Restart Docker services |
| `make logs` | `make docker-logs` | View Docker logs |
| `make shell` | `make docker-shell` | Open shell in container |
| `make test` (Docker) | `make docker-test` | Run tests in container |
| `make ingest` (Docker) | `make docker-ingest` | Run ingestion in container |
| `make clean` (Docker) | `make docker-clean` | Remove containers and volumes |
| `make rebuild` | `make docker-rebuild` | Rebuild and restart |
| `make dev` | `make docker-dev` | Start in development mode |
| `make format` (Docker) | `make docker-format` | Format code in container |
| `make lint` (Docker) | `make docker-lint` | Lint code in container |
| `make backup` | `make docker-backup` | Backup Docker volumes |
| `make restore` | `make docker-restore` | Restore Docker volumes |
| `make status` | `make docker-status` | Show container status |
| `make stats` | `make docker-stats` | Show resource usage |
| `make up-nginx` | `make docker-up-nginx` | Start with nginx |

### Local Development Commands (Unchanged)

These commands remain the same and work with Poetry for local development:

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install production dependencies |
| `make install-dev` | Install dev dependencies |
| `make setup` | Run initial setup script |
| `make clean` | Clean generated files |
| `make format` | Format code with ruff |
| `make lint` | Lint code with ruff |
| `make type-check` | Run mypy type checking |
| `make security` | Run bandit security checks |
| `make test` | Run tests locally |
| `make test-cov` | Run tests with coverage |
| `make pre-commit` | Run pre-commit hooks |
| `make check` | Run all quality checks |
| `make ingest` | Run ingestion locally |
| `make ingest-dry-run` | Validate data without ingesting |
| `make rag` | Start interactive REPL |
| `make rag-question` | Ask a single question |
| `make update` | Update dependencies |
| `make lock` | Update lock file |
| `make shell` | Start poetry shell |
| `make zip` | Create project archive |
| `make zip-manual` | Create manual archive |

## Quick Reference

### For Docker Users

```bash
# Start services
make docker-up

# View logs
make docker-logs

# Run tests
make docker-test

# Stop services
make docker-down
```

### For Local Development

```bash
# Install dependencies
make install-dev

# Run tests
make test

# Format and lint
make format
make lint

# Run all checks
make check
```

## Help Commands

- `make help` - Show all commands (both local and Docker)
- `make docker-help` - Show Docker-specific commands only

## Migration Checklist

- [x] All Docker commands prefixed with `docker-`
- [x] Local development commands preserved
- [x] README.md updated with new commands
- [x] DOCKER.md updated with new commands
- [x] Help text updated to show both sections
- [x] Backward compatibility maintained for local commands

## Notes

- **Local commands** use Poetry and run on your host machine
- **Docker commands** run inside containers and don't require local Python setup
- Both workflows are fully supported and can be used interchangeably
- GitHub Actions workflows use Poetry directly (not affected by this change)

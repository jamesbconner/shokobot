# Docker Deployment Guide

This guide covers deploying ShokoBot using Docker and Docker Compose.

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- OpenAI API key

### Basic Deployment

1. **Create environment file**:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

2. **Build and run**:
```bash
docker-compose up -d
```

3. **Access the web UI**:
```
http://localhost:7860
```

## Configuration

### Dependency Management

The Docker image uses **pip** to install from `pyproject.toml`:
- Dependencies are defined in `pyproject.toml` (PEP 621 format)
- The package and all dependencies are installed with `pip install .`
- Only production dependencies are installed (dev dependencies excluded)
- No need to manually update Dockerfile when dependencies change
- Compatible with both Poetry and uv for local development

### Security

**Important:** The `.dockerignore` file excludes all `.env` files to prevent secrets from being baked into the image:
- `.env` files are never copied into the Docker image
- Secrets are passed at runtime via `docker-compose.yml` env_file directive
- This prevents API keys from being exposed in image layers

### Environment Variables

Required:
- `OPENAI_API_KEY` - Your OpenAI API key

Optional (see `config.json` for defaults):
- `SHOKOBOT_MODEL` - OpenAI model (default: gpt-5-nano)
- `SHOKOBOT_CHROMA_DIR` - ChromaDB directory (default: .chroma)
- `SHOKOBOT_DATA_DIR` - Data directory (default: data)

### Volume Mounts

The docker-compose.yml defines several volumes:

- `./data:/app/data` - Data directory for MCP cache and other runtime data
- `chroma_data:/app/.chroma` - Vector database (Docker-managed named volume)
- `./resources:/app/resources` - Configuration files including `config.json` (read-only)
- `./input:/app/input` - Input data files for ingestion (read-only)
- `mcp_cache:/app/data/mcp_cache` - MCP cache (Docker-managed named volume)

**Named Volumes vs Bind Mounts:**
- Named volumes (`chroma_data`, `mcp_cache`) are managed by Docker and persist independently
- Bind mounts (`./resources`, `./input`) map directly to host directories
- Named volumes are better for data that doesn't need direct host access
- Use `docker volume ls` to see all volumes and `docker volume inspect <name>` for details

## Usage

### Start Services

```bash
# Start in background
docker-compose up -d

# Start with logs
docker-compose up

# Start with nginx reverse proxy
docker-compose --profile with-nginx up -d
```

### Stop Services

```bash
# Stop containers
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f shokobot

# Last 100 lines
docker-compose logs --tail=100 shokobot
```

### View Image Metadata

The Docker image includes OCI-compliant labels with build information (version, git commit, build date):

```bash
# View all image labels
docker inspect ghcr.io/jamesbconner/shokobot:latest | jq '.[0].Config.Labels'

# View specific metadata
docker inspect ghcr.io/jamesbconner/shokobot:latest | jq '.[0].Config.Labels."org.opencontainers.image.version"'
docker inspect ghcr.io/jamesbconner/shokobot:latest | jq '.[0].Config.Labels."org.opencontainers.image.revision"'
docker inspect ghcr.io/jamesbconner/shokobot:latest | jq '.[0].Config.Labels."org.opencontainers.image.created"'
```

These labels are automatically populated during CI/CD builds and help with:
- Version tracking and auditing
- Identifying which git commit an image was built from
- Debugging production issues

### Execute Commands

```bash
# Run CLI commands
docker-compose exec shokobot shokobot --help

# Ingest data
docker-compose exec shokobot shokobot ingest input/shoko_tvshows.json

# Query the database
docker-compose exec shokobot shokobot query -q "Best mecha anime"

# Interactive shell
docker-compose exec shokobot bash

# Run REPL
docker-compose exec shokobot shokobot repl

# Run as root (for troubleshooting)
docker-compose exec -u root shokobot bash
```

**Available CLI commands:**
- `shokobot web` - Start web interface (supports `--port`, `--share`, `--debug`)
- `shokobot ingest` - Ingest anime data from JSON file
- `shokobot query` - Query the database from command line
- `shokobot repl` - Interactive REPL mode
- `shokobot info` - Display system information

## Advanced Configuration

### Custom Dockerfile

For development, create `Dockerfile.dev`:

```dockerfile
FROM python:3.13.9-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY . .

# Install package with dev dependencies
RUN pip install -e ".[dev]"

# Development mode
CMD ["shokobot", "web", "--debug"]
```

### Docker Compose Override

For local development customization, create `docker-compose.override.yml` from the example:

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
# Edit as needed for your local setup
```

This file is automatically loaded by docker-compose and is git-ignored.

The example override mounts source code directories for hot reload during development:

```yaml
version: '3.8'

services:
  shokobot:
    volumes:
      # Mount source directories for live code updates
      - ./cli:/app/cli
      - ./services:/app/services
      - ./models:/app/models
      - ./utils:/app/utils
      - ./prompts:/app/prompts
      - ./ui:/app/ui
    environment:
      - DEBUG=1
      - LOG_LEVEL=DEBUG
```

**How it works:**
- The base image has all Python packages installed
- Source code directories are mounted over the image's code
- Changes to Python files are reflected immediately (no rebuild needed)
- Dependencies remain in the image (no need for local venv)

Then start in development mode:

```bash
make docker-dev
# or
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

**Development workflow:**
1. Make code changes in your editor
2. Restart the container to see changes: `docker-compose restart shokobot`
3. For dependency changes, rebuild: `docker-compose build`

**Note:** The `shokobot web` command supports these flags:
- `--port <number>` - Port to run on (default: 7860)
- `--share` - Create public Gradio link
- `--debug` - Enable verbose logging

The server always listens on `0.0.0.0` (all interfaces) by default.

### Resource Limits

Adjust in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Max CPUs
      memory: 8G     # Max memory
    reservations:
      cpus: '2'      # Reserved CPUs
      memory: 4G     # Reserved memory
```

## Production Deployment

### With Nginx Reverse Proxy

1. **Configure SSL certificates**:
```bash
mkdir -p ssl
# Add your cert.pem and key.pem to ssl/
```

2. **Update nginx.conf** with your domain

3. **Start with nginx**:
```bash
docker-compose --profile with-nginx up -d
```

### Security Best Practices

1. **Use secrets for API keys**:
```yaml
services:
  shokobot:
    secrets:
      - openai_api_key
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/openai_api_key

secrets:
  openai_api_key:
    file: ./secrets/openai_api_key.txt
```

2. **Run as non-root** (already configured in Dockerfile)

3. **Use read-only filesystem where possible**:
```yaml
services:
  shokobot:
    read_only: true
    tmpfs:
      - /tmp
```

4. **Enable security scanning**:
```bash
docker scan shokobot:latest
```

### Health Monitoring

The container includes a health check. Monitor with:

```bash
# Check health status
docker-compose ps

# View health check logs
docker inspect --format='{{json .State.Health}}' shokobot | jq
```

### Backup and Restore

> **Note:** Docker Compose automatically prefixes volume names with the project name (directory name by default). For example, if your project directory is `ShokoBot`, volumes will be named `shokobot_chroma_data` and `shokobot_mcp_cache`. Use `docker volume ls` to see the actual volume names.

**Backup volumes**:
```bash
# First, find the actual volume names (Docker Compose prefixes with project name)
docker volume ls | grep chroma_data
docker volume ls | grep mcp_cache

# Backup ChromaDB (replace <project>_chroma_data with actual volume name)
VOLUME_NAME=$(docker volume ls --format '{{.Name}}' | grep chroma_data)
docker run --rm -v $VOLUME_NAME:/data -v $(pwd):/backup \
  alpine tar czf /backup/chroma_backup.tar.gz -C /data .

# Backup MCP cache
VOLUME_NAME=$(docker volume ls --format '{{.Name}}' | grep mcp_cache)
docker run --rm -v $VOLUME_NAME:/data -v $(pwd):/backup \
  alpine tar czf /backup/mcp_backup.tar.gz -C /data .

# Or use the Makefile command (automatically finds the correct volume)
make docker-backup
```

**Restore volumes**:
```bash
# Restore ChromaDB (replace <project>_chroma_data with actual volume name)
VOLUME_NAME=$(docker volume ls --format '{{.Name}}' | grep chroma_data)
docker run --rm -v $VOLUME_NAME:/data -v $(pwd):/backup \
  alpine tar xzf /backup/chroma_backup.tar.gz -C /data

# Restore MCP cache
VOLUME_NAME=$(docker volume ls --format '{{.Name}}' | grep mcp_cache)
docker run --rm -v $VOLUME_NAME:/data -v $(pwd):/backup \
  alpine tar xzf /backup/mcp_backup.tar.gz -C /data

# Or use the Makefile command (automatically finds the correct volume)
make docker-restore BACKUP=backups/chroma_20240101_120000.tar.gz
```

## Common Issues

### Development Mode Setup

If `make docker-dev` fails with "file not found":
```bash
# Create the override file from the example
cp docker-compose.override.yml.example docker-compose.override.yml
# Then try again
make docker-dev
```

### Volume Naming

Docker Compose prefixes volume names with the project directory name. If backup/restore commands fail:
```bash
# List actual volume names
docker volume ls | grep chroma

# Use the Makefile commands which auto-detect volumes
make docker-backup
make docker-restore BACKUP=backups/chroma_20240101_120000.tar.gz
```

### CLI Command Errors

The `shokobot web` command only supports these flags:
- `--port` - Port number (default: 7860)
- `--share` - Create public link
- `--debug` - Enable debug logging

**Invalid flags** (will cause errors):
- `--host` - Not supported (always listens on 0.0.0.0)
- `--reload` - Not supported (use volume mounts for hot reload)

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs shokobot

# Check container status
docker-compose ps

# Inspect container
docker inspect shokobot

# View image metadata and labels
docker inspect ghcr.io/jamesbconner/shokobot:latest | jq '.[0].Config.Labels'
```

### Permission issues

```bash
# Fix volume permissions (requires root)
docker-compose exec -u root shokobot chown -R shokobot:shokobot /app/data /app/.chroma
```

### Out of memory

```bash
# Check memory usage
docker stats shokobot

# Increase memory limit in docker-compose.yml
```

### Network issues

```bash
# Check network
docker network inspect shokobot_shokobot-network

# Restart networking
docker-compose down
docker-compose up -d
```

## Building for Multiple Architectures

Build for ARM64 and AMD64:

```bash
# Setup buildx
docker buildx create --name multiarch --use

# Build and push
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourusername/shokobot:latest \
  --push .
```

## CI/CD Integration

### GitHub Actions Workflow

This project includes a complete GitHub Actions workflow (`.github/workflows/docker.yml`) that:

1. **Builds and scans images** for security vulnerabilities using Trivy
2. **Publishes to GitHub Container Registry** (ghcr.io) on push to main/develop
3. **Supports multi-platform builds** (linux/amd64, linux/arm64)
4. **Uses GitHub Actions cache** for faster builds
5. **Runs tests** on pull requests before merging

**Key features:**
- Single-platform build for security scanning (Trivy can't scan multi-platform manifests)
- Multi-platform build for production deployment
- Automatic tagging based on branch/tag/commit
- Security scan results uploaded to GitHub Security tab
- Build cache shared across workflows for speed

**Workflow triggers:**
- Push to `main` or `develop` branches
- Push tags matching `v*` pattern
- Pull requests to `main` branch

**Published images:**
- `ghcr.io/jamesbconner/shokobot:latest` - Latest main branch
- `ghcr.io/jamesbconner/shokobot:main` - Main branch
- `ghcr.io/jamesbconner/shokobot:develop` - Develop branch
- `ghcr.io/jamesbconner/shokobot:sha-<commit>` - Specific commit
- `ghcr.io/jamesbconner/shokobot:v1.0.0` - Version tags

## Performance Tuning

### Optimize Image Size

Current image size: ~500MB (slim base + dependencies)

The Dockerfile uses:
- Multi-stage build to separate build and runtime dependencies
- pip for dependency management (reads from pyproject.toml and poetry.lock)
- Python 3.13.9-slim base image
- Only production dependencies (no dev dependencies)
- Proper `.dockerignore` to exclude unnecessary files

**Image layers:**
1. Base Python image (~150MB)
2. System dependencies (build-essential, curl)
3. Python packages (~300MB)
4. Application code (~50MB)

To reduce further:
- Use `python:3.13-alpine` (adds complexity with build deps)
- Remove unnecessary dependencies from pyproject.toml
- Use `--no-cache-dir` with pip (already done)

### Optimize Runtime

1. **Use gunicorn for production**:
```dockerfile
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:7860", "cli.web:app"]
```

2. **Enable caching**:
```yaml
environment:
  - PYTHONPYCACHEPREFIX=/tmp/pycache
```

3. **Use tmpfs for temporary files**:
```yaml
tmpfs:
  - /tmp:size=1G
```

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best Practices for Writing Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

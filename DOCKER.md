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
- `chroma_data:/app/.chroma` - Vector database (persistent named volume)
- `./resources:/app/resources` - Configuration files (read-only)
- `./input:/app/input` - Input data files for ingestion (read-only)
- `mcp_cache:/app/data/mcp_cache` - MCP cache (optional named volume)

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

The Docker image includes OCI-compliant labels with build information:

```bash
# View all image labels
docker inspect ghcr.io/jamesbconner/shokobot:latest | jq '.[0].Config.Labels'

# View specific metadata
docker inspect ghcr.io/jamesbconner/shokobot:latest | jq '.[0].Config.Labels."org.opencontainers.image.version"'
docker inspect ghcr.io/jamesbconner/shokobot:latest | jq '.[0].Config.Labels."org.opencontainers.image.revision"'
docker inspect ghcr.io/jamesbconner/shokobot:latest | jq '.[0].Config.Labels."org.opencontainers.image.created"'
```

### Execute Commands

```bash
# Run CLI commands
docker-compose exec shokobot shokobot --help

# Ingest data
docker-compose exec shokobot shokobot ingest input/shoko_tvshows.json

# Interactive shell
docker-compose exec shokobot bash

# Run REPL
docker-compose exec shokobot shokobot repl
```

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
make dev
# or
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

**Note:** For dependency changes, rebuild the image:
```bash
docker-compose build
```

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
make backup
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
make restore BACKUP=backups/chroma_20240101_120000.tar.gz
```

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
# Fix volume permissions
docker-compose exec shokobot chown -R shokobot:shokobot /app/data /app/.chroma
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

### GitHub Actions Example

```yaml
name: Docker Build

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            yourusername/shokobot:latest
            yourusername/shokobot:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Performance Tuning

### Optimize Image Size

Current image size: ~500MB (slim base + dependencies)

The Dockerfile uses:
- Multi-stage build to separate build and runtime dependencies
- Poetry for dependency management (reads from pyproject.toml and poetry.lock)
- Python 3.13.9-slim base image
- Only production dependencies (no dev dependencies)

To reduce further:
- Use `python:3.13-alpine` (adds complexity with build deps)
- Remove unnecessary dependencies from pyproject.toml

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

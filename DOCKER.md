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

### Environment Variables

Required:
- `OPENAI_API_KEY` - Your OpenAI API key

Optional (see `config.json` for defaults):
- `SHOKOBOT_MODEL` - OpenAI model (default: gpt-5-nano)
- `SHOKOBOT_CHROMA_DIR` - ChromaDB directory (default: .chroma)
- `SHOKOBOT_DATA_DIR` - Data directory (default: data)

### Volume Mounts

The docker-compose.yml defines several volumes:

- `./data:/data` - Anime data files
- `chroma_data:/app/.chroma` - Vector database (persistent)
- `./config.json:/app/config.json` - Configuration file
- `mcp_cache:/app/data/mcp_cache` - MCP cache (optional)

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

### Execute Commands

```bash
# Run CLI commands
docker-compose exec shokobot python -m cli.main --help

# Ingest data
docker-compose exec shokobot python -m cli.main ingest data/anime.json

# Interactive shell
docker-compose exec shokobot bash

# Run REPL
docker-compose exec shokobot python -m cli.main repl
```

## Advanced Configuration

### Custom Dockerfile

For development, create `Dockerfile.dev`:

```dockerfile
FROM python:3.13.9-slim

WORKDIR /app

# Install dependencies
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# Copy source
COPY . .

# Development mode
CMD ["poetry", "run", "python", "-m", "cli.web", "--reload"]
```

### Docker Compose Override

Create `docker-compose.override.yml` for local customization:

```yaml
version: '3.8'

services:
  shokobot:
    build:
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app  # Mount source for hot reload
    environment:
      - DEBUG=1
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

**Backup volumes**:
```bash
# Backup ChromaDB
docker run --rm -v shokobot_chroma_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/chroma_backup.tar.gz -C /data .

# Backup MCP cache
docker run --rm -v shokobot_mcp_cache:/data -v $(pwd):/backup \
  alpine tar czf /backup/mcp_backup.tar.gz -C /data .
```

**Restore volumes**:
```bash
# Restore ChromaDB
docker run --rm -v shokobot_chroma_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/chroma_backup.tar.gz -C /data

# Restore MCP cache
docker run --rm -v shokobot_mcp_cache:/data -v $(pwd):/backup \
  alpine tar xzf /backup/mcp_backup.tar.gz -C /data
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
```

### Permission issues

```bash
# Fix volume permissions
docker-compose exec shokobot chown -R shokobot:shokobot /data /app/.chroma
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

To reduce further:
- Use `python:3.12-alpine` (adds complexity with build deps)
- Multi-stage build (already implemented)
- Remove unnecessary dependencies

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

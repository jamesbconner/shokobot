#!/bin/bash
# Setup script for Shokobot

set -e

echo "🤖 Shokobot Setup"
echo "================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.12"

if ! python -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)"; then
    echo "❌ Python 3.12+ is required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version"
echo ""

# Check for Poetry or uv
echo "Checking for package manager..."
if command -v poetry &> /dev/null; then
    echo "✓ Poetry found"
    PKG_MANAGER="poetry"
elif command -v uv &> /dev/null; then
    echo "✓ uv found"
    PKG_MANAGER="uv"
else
    echo "❌ Neither Poetry nor uv found."
    echo ""
    echo "Install Poetry:"
    echo "  curl -sSL https://install.python-poetry.org | python3 -"
    echo ""
    echo "Or install uv:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo ""

# Install dependencies
echo "Installing dependencies..."
if [ "$PKG_MANAGER" = "poetry" ]; then
    poetry install --with dev
elif [ "$PKG_MANAGER" = "uv" ]; then
    uv venv
    source .venv/bin/activate
    uv pip install -e ".[dev]"
fi
echo "✓ Dependencies installed"
echo ""

# Setup .env file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
else
    echo "✓ .env file already exists"
fi
echo ""

# Setup pre-commit hooks
if [ "$PKG_MANAGER" = "poetry" ]; then
    echo "Installing pre-commit hooks..."
    poetry run pre-commit install
    echo "✓ Pre-commit hooks installed"
    echo ""
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p .chroma logs
echo "✓ Directories created"
echo ""

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OPENAI_API_KEY"
echo "2. Place your anime data in resources/tvshows.json"
echo "3. Run ingestion: poetry run shokobot-ingest"
echo "4. Start querying: poetry run shokobot-rag --repl"

#!/bin/bash
# Setup script for ShokoBot

set -e

echo "🤖 ShokoBot Setup"
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
    echo "Install Poetry (for build system):"
    echo "  curl -sSL https://install.python-poetry.org | python3 -"
    echo ""
    echo "Or install uv (for dependency management):"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  # Or via pip: pip install uv"
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
elif [ "$PKG_MANAGER" = "uv" ]; then
    echo "Installing pre-commit hooks..."
    uv run pre-commit install
    echo "✓ Pre-commit hooks installed"
    echo ""
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p .chroma logs input
echo "✓ Directories created"
echo ""

# Verify configuration
echo "Verifying configuration..."
if [ -f "resources/config.json" ]; then
    echo "✓ Configuration file found"
else
    echo "⚠️  Configuration file not found at resources/config.json"
fi

if [ -f "input/shoko_tvshows.json" ]; then
    echo "✓ Anime data file found"
else
    echo "⚠️  Anime data file not found at input/shoko_tvshows.json"
    echo "   Place your Shoko export file there before ingesting"
fi
echo ""

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OPENAI_API_KEY"
echo "   export OPENAI_API_KEY='your-key-here'"
echo ""
echo "2. Verify configuration:"
if [ "$PKG_MANAGER" = "poetry" ]; then
    echo "   poetry run shokobot info"
elif [ "$PKG_MANAGER" = "uv" ]; then
    echo "   uv run shokobot info"
fi
echo ""
echo "3. Place your anime data in input/shoko_tvshows.json (if not already present)"
echo ""
echo "4. Run ingestion:"
if [ "$PKG_MANAGER" = "poetry" ]; then
    echo "   poetry run shokobot ingest"
elif [ "$PKG_MANAGER" = "uv" ]; then
    echo "   uv run shokobot ingest"
fi
echo ""
echo "5. Start querying:"
if [ "$PKG_MANAGER" = "poetry" ]; then
    echo "   poetry run shokobot repl          # Interactive REPL mode"
    echo "   poetry run shokobot query -q \"...\" # Single question"
elif [ "$PKG_MANAGER" = "uv" ]; then
    echo "   uv run shokobot repl              # Interactive REPL mode"
    echo "   uv run shokobot query -q \"...\"     # Single question"
fi
echo ""
echo "For more information, see:"
echo "  - README.md for project overview"
echo "  - SETUP_GUIDE.md for detailed setup instructions"
echo "  - QUICK_REFERENCE.md for command reference"

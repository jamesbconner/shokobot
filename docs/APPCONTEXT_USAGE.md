# AppContext Usage Guide

This guide shows how to use `AppContext` for dependency injection in CLI commands and services.

## Overview

`AppContext` is a centralized container for shared services and configuration. It provides:

- **Single source of truth** for configuration
- **Lazy initialization** of expensive resources
- **Easy testing** through dependency injection
- **Clean separation** between CLI and business logic

## Basic Usage

### Creating AppContext

```python
from services.app_context import AppContext

# Create with default config path
ctx = AppContext.create()

# Create with custom config path
ctx = AppContext.create("custom/config.json")

# Access configuration
model = ctx.config.get("openai.model")
batch_size = ctx.config.get("ingest.batch_size", 100)
```

## Using in CLI Commands

### Pattern 1: Pass AppContext to Functions

```python
# cli/example.py
import rich_click as click
from services.app_context import AppContext
from services.example_service import do_something

@click.command()
@click.option("--config", default="resources/config.json", help="Config file path")
def example(config: str) -> None:
    """Example command using AppContext."""
    ctx = AppContext.create(config)
    
    # Pass context to service functions
    result = do_something(ctx)
    
    click.echo(f"Result: {result}")
```

### Pattern 2: Use Click Context (Recommended)

```python
# cli/__init__.py
import rich_click as click
from services.app_context import AppContext

@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ShokoBot CLI."""
    # Store AppContext in Click context
    ctx.obj = AppContext.create()

# cli/example.py
from typing import TYPE_CHECKING

import rich_click as click

if TYPE_CHECKING:
    from services.app_context import AppContext

@click.command()
@click.pass_obj
def example(ctx: "AppContext") -> None:
    """Example command with injected context."""
    model = ctx.config.get("openai.model")
    click.echo(f"Using model: {model}")
```

## Extending AppContext

### Adding Service Properties

```python
# services/app_context.py
from dataclasses import dataclass, field
from langchain_chroma import Chroma

from services.config_service import ConfigService

@dataclass
class AppContext:
    """Application context containing shared configuration and services."""
    
    config: ConfigService
    _vectorstore: Chroma | None = field(default=None, init=False, repr=False)
    
    @classmethod
    def create(cls, config_path: str = "resources/config.json") -> "AppContext":
        """Create application context with configuration."""
        config = ConfigService(config_path)
        return cls(config=config)
    
    @property
    def vectorstore(self) -> Chroma:
        """Get or create vectorstore instance (lazy initialization)."""
        if self._vectorstore is None:
            from services.vectorstore_service import get_chroma_vectorstore
            
            self._vectorstore = get_chroma_vectorstore(self.config)
        return self._vectorstore
```

### Using Lazy-Loaded Services

```python
# cli/query.py
from typing import TYPE_CHECKING

import rich_click as click

if TYPE_CHECKING:
    from services.app_context import AppContext

@click.command()
@click.option("-q", "--question", help="Question to ask")
@click.pass_obj
def query(ctx: "AppContext", question: str) -> None:
    """Query the anime database."""
    # RAG chain is created only when first accessed (includes vectorstore)
    rag_chain = ctx.rag_chain
    
    # Execute query
    answer, docs = rag_chain(question)
    click.echo(answer)
```

## Service Functions with AppContext

### Pattern: Accept AppContext Parameter

```python
# services/example_service.py
from services.app_context import AppContext
from services.vectorstore_service import get_chroma_vectorstore

def process_data(ctx: AppContext, data: list[dict]) -> None:
    """Process data using services from context.
    
    Args:
        ctx: Application context with configuration and services.
        data: Data to process.
    """
    # Get configuration
    batch_size = ctx.config.get("ingest.batch_size", 100)
    
    # Get or create vectorstore
    vectorstore = ctx.vectorstore
    
    # Process in batches
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        # Process batch...
```

## Testing with AppContext

### Mock Configuration

```python
# tests/test_example.py
import pytest
from services.app_context import AppContext
from services.config_service import ConfigService

@pytest.fixture
def test_context():
    """Create test context with mock configuration."""
    config = ConfigService("tests/fixtures/test_config.json")
    return AppContext(config=config)

def test_example_service(test_context):
    """Test service with injected context."""
    from services.example_service import do_something
    
    result = do_something(test_context)
    assert result is not None
```

### Mock Services

```python
# tests/test_with_mocks.py
import pytest
from unittest.mock import Mock
from services.app_context import AppContext

@pytest.fixture
def mock_context():
    """Create context with mocked services."""
    ctx = Mock(spec=AppContext)
    ctx.config = Mock()
    ctx.config.get.return_value = "test-value"
    ctx.vectorstore = Mock()
    return ctx

def test_with_mock_context(mock_context):
    """Test with fully mocked context."""
    from services.example_service import do_something
    
    result = do_something(mock_context)
    mock_context.config.get.assert_called_once()
```

## Best Practices

### Do's ✓

- **Create once** - Create AppContext at CLI entry point
- **Pass down** - Pass context to services that need it
- **Lazy load** - Use properties for expensive resources
- **Type hints** - Always type hint AppContext parameters
- **Test friendly** - Design services to accept AppContext
- **Reset after changes** - Call `ctx.reset_all()` after ingestion or state changes
- **Use TYPE_CHECKING** - Import AppContext in TYPE_CHECKING block to avoid circular imports

### Don'ts ✗

- **Don't create multiple** - One AppContext per CLI invocation
- **Don't store state** - AppContext is for services, not application state
- **Don't import globally** - Pass as parameter, don't import in services
- **Don't mix concerns** - Keep business logic in services, not AppContext
- **Don't cache mutable state** - Only cache service instances, not data

## Benefits Achieved

### 1. Performance - Caching & Lazy Loading

**Before**: Every call created new instances
```python
# Each query created new vectorstore and embeddings
rag = build_rag_chain(config)  # Creates new vectorstore
rag = build_rag_chain(config)  # Creates ANOTHER new vectorstore
```

**After**: Instances are cached
```python
# First call creates, subsequent calls reuse
rag = ctx.rag_chain  # Creates vectorstore
rag = ctx.rag_chain  # Reuses same vectorstore
```

**Benefits**:
- ✓ Faster subsequent operations (especially in REPL mode)
- ✓ Reduced memory usage
- ✓ Fewer API calls to OpenAI embeddings

### 2. Simplified Testing

**Before**: Mock multiple dependencies
```python
def test_ingest():
    config = Mock(spec=ConfigService)
    config.get.side_effect = lambda key, default=None: {...}
    
    with patch('services.ingest_service.upsert_documents'):
        result = ingest_showdocs_streaming(docs, config, batch_size=10)
```

**After**: Mock single context
```python
def test_ingest():
    ctx = Mock(spec=AppContext)
    ctx.config.get.return_value = 100
    ctx.vectorstore = Mock()
    
    result = ingest_showdocs_streaming(docs, ctx, batch_size=10)
```

**Benefits**:
- ✓ Single mock point
- ✓ Easier to create test fixtures
- ✓ More flexible test scenarios

### 3. Centralized Service Management

**Before**: Services created ad-hoc
```python
# Different parts of code create services independently
vs = get_chroma_vectorstore(config)
rag = build_rag_chain(config)
```

**After**: Single point of creation
```python
# All services created through context
vs = ctx.vectorstore
rag = ctx.rag_chain
```

**Benefits**:
- ✓ Single source of truth
- ✓ Consistent initialization
- ✓ Easy to add new services (like MCP client)

### 4. Cleaner CLI Commands

**Before**: Dictionary lookups and multiple imports
```python
@click.pass_context
def query(ctx: click.Context, ...):
    config: ConfigService = ctx.obj["config"]
    console: Console = ctx.obj["console"]
    rag = build_rag_chain(config)
```

**After**: Type-safe context access
```python
@click.pass_obj
def query(ctx: "AppContext", ...):
    console = Console()
    rag = ctx.rag_chain  # Lazy-loaded and cached
```

**Benefits**:
- ✓ Type-safe access
- ✓ No dictionary lookups
- ✓ Clearer dependencies

## Migration Example

### Before (Direct Service Calls)

```python
# cli/ingest.py
import rich_click as click
from services.config_service import ConfigService
from services.ingest_service import ingest_showdocs_streaming, iter_showdocs_from_json
from services.vectorstore_service import get_chroma_vectorstore

@click.command()
@click.pass_context
def ingest(ctx: click.Context) -> None:
    """Ingest anime data."""
    config: ConfigService = ctx.obj["config"]
    docs_iter = iter_showdocs_from_json(config)
    ingest_showdocs_streaming(docs_iter, config)
```

### After (With AppContext)

```python
# cli/ingest.py
from typing import TYPE_CHECKING

import rich_click as click

if TYPE_CHECKING:
    from services.app_context import AppContext

@click.command()
@click.pass_obj
def ingest(ctx: "AppContext") -> None:
    """Ingest anime data."""
    from services.ingest_service import ingest_showdocs_streaming, iter_showdocs_from_json
    
    docs_iter = iter_showdocs_from_json(ctx)
    ingest_showdocs_streaming(docs_iter, ctx)
    
    # Reset cached services after ingestion
    ctx.reset_all()

# services/ingest_service.py
def ingest_showdocs_streaming(docs_iter, ctx: "AppContext") -> int:
    """Ingest shows using context services."""
    batch_size = ctx.config.get("ingest.batch_size", 100)
    # Uses ctx.vectorstore via upsert_documents
    # ... rest of implementation
```

## Future Enhancements

### Adding MCP Server Support

```python
# services/app_context.py
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.mcp_client import MCPClient

@dataclass
class AppContext:
    config: ConfigService
    _vectorstore: Chroma | None = field(default=None, init=False, repr=False)
    _mcp_client: "MCPClient | None" = field(default=None, init=False, repr=False)
    
    @property
    def mcp_client(self) -> "MCPClient":
        """Get or create MCP client for AniDB API."""
        if self._mcp_client is None:
            from services.mcp_client import MCPClient
            
            self._mcp_client = MCPClient(self.config)
        return self._mcp_client
```

### Adding Caching

```python
# services/app_context.py
from functools import lru_cache

@dataclass
class AppContext:
    config: ConfigService
    
    @property
    @lru_cache(maxsize=1)
    def vectorstore(self) -> Chroma:
        """Get cached vectorstore instance."""
        return get_chroma_vectorstore(self.config)
```

## See Also

- [MODULAR_CLI_ARCHITECTURE.md](MODULAR_CLI_ARCHITECTURE.md) - CLI design patterns and auto-loading
- [ASYNC_OPPORTUNITIES_ANALYSIS.md](ASYNC_OPPORTUNITIES_ANALYSIS.md) - Performance optimization opportunities

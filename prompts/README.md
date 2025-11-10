# Prompt Templates

This directory contains all LLM prompt templates used in ShokoBot, following best practices for prompt engineering and version control.

## Structure

```
prompts/
├── __init__.py      # Exports for easy importing
├── anime_rag.py     # Anime RAG query prompts
└── README.md        # This file
```

## Design Principles

### 1. Separation of Concerns
Prompts are separated from business logic, making them:
- Easy to modify without changing code
- Simple to test independently
- Version controlled with clear history
- Reviewable by non-developers

### 2. Versioning
Each prompt includes:
- Version number
- Last updated date
- Purpose description
- Usage guidelines

### 3. Multiple Variants
Different prompts for different use cases:
- `build_anime_rag_prompt()` - Standard balanced responses
- `build_detailed_anime_prompt()` - Comprehensive analysis
- `build_recommendation_prompt()` - Concise recommendations

## Usage

### Basic Usage

```python
from prompts import build_anime_rag_prompt

# Get the prompt template
prompt = build_anime_rag_prompt()

# Use with LangChain
messages = prompt.format_messages(
    question="What is Cowboy Bebop about?",
    context="Cowboy Bebop: A space western anime..."
)
```

### In Services

```python
# services/rag_service.py
from prompts import build_anime_rag_prompt

def build_rag_chain(ctx: "AppContext") -> Callable:
    llm = ChatOpenAI(...)
    prompt = build_anime_rag_prompt()  # Load from prompts module
    # ... rest of chain
```

## Adding New Prompts

### 1. Define the Prompt

```python
# prompts/anime_rag.py

# Version: 1.1
# Last Updated: 2025-11-10
# Purpose: Brief description
NEW_PROMPT = """Your prompt text here..."""

def build_new_prompt() -> ChatPromptTemplate:
    """Build the new prompt template.
    
    Returns:
        ChatPromptTemplate configured for specific use case.
    """
    return ChatPromptTemplate.from_messages([
        ("system", NEW_PROMPT),
        ("human", "{question}\n\nContext:\n{context}"),
    ])
```

### 2. Export in __init__.py

```python
# prompts/__init__.py
from prompts.anime_rag import build_new_prompt

__all__ = [
    "build_anime_rag_prompt",
    "build_new_prompt",  # Add new export
]
```

### 3. Use in Services

```python
from prompts import build_new_prompt

prompt = build_new_prompt()
```

## Testing Prompts

### Unit Testing

```python
# tests/test_prompts.py
from prompts import build_anime_rag_prompt

def test_anime_rag_prompt():
    prompt = build_anime_rag_prompt()
    
    # Test formatting
    messages = prompt.format_messages(
        question="Test question",
        context="Test context"
    )
    
    assert len(messages) == 2
    assert messages[0].type == "system"
    assert messages[1].type == "human"
```

### Manual Testing

```python
# Test prompt output
from prompts import build_anime_rag_prompt
from langchain_openai import ChatOpenAI

prompt = build_anime_rag_prompt()
llm = ChatOpenAI(model="gpt-5-nano")

messages = prompt.format_messages(
    question="What is Cowboy Bebop?",
    context="Cowboy Bebop: A 1998 space western anime..."
)

response = llm.invoke(messages)
print(response.content)
```

## Best Practices

### 1. Clear Instructions
- Be explicit about what the LLM should do
- Provide examples when helpful
- Specify output format if needed

### 2. Context Handling
- Explain the context format
- Guide how to use the context
- Handle missing information gracefully

### 3. Constraints
- Specify what NOT to do
- Set boundaries (e.g., "use ONLY provided context")
- Handle edge cases

### 4. Versioning
- Update version number when changing prompts
- Document the change reason
- Keep old versions commented if needed for reference

### 5. Testing
- Test with various inputs
- Verify output format
- Check edge cases (empty context, ambiguous questions)

## Current Prompts

### anime_rag.py

**build_anime_rag_prompt()** (v1.0)
- Purpose: Standard anime queries with balanced responses
- Use case: General questions about anime
- Output: Concise, informative answers

**build_detailed_anime_prompt()** (v1.0)
- Purpose: Comprehensive anime analysis
- Use case: When users want detailed information
- Output: Structured, detailed responses with reasoning

**build_recommendation_prompt()** (v1.0)
- Purpose: Anime recommendations
- Use case: "What should I watch?" type questions
- Output: List format with brief justifications

## Configuration

Prompts can be selected via configuration:

```json
{
  "rag": {
    "prompt_type": "standard",  // or "detailed", "recommendation"
    "custom_prompt_path": null  // optional: load from file
  }
}
```

## Future Enhancements

- [ ] Load prompts from external files (YAML/JSON)
- [ ] A/B testing framework for prompt variants
- [ ] Prompt performance metrics
- [ ] User-customizable prompts
- [ ] Multi-language prompt support

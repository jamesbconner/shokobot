# JSON Output Format Feature

## Overview
Added support for structured JSON output format to enable programmatic usage of ShokoBot by other services.

## Changes Made

### 1. RAG Service (`services/rag_service.py`)
- Added `output_format` parameter to `build_rag_chain()` function (default: "text")
- Created `_init_llm()` helper function that returns both LLM and prompt:
  - For JSON format: explicitly passes `response_format={"type": "json_object"}` parameter
  - For text format: uses standard initialization
  - Avoids kwargs warnings by using explicit parameter names instead of `**kwargs`
  - Returns appropriate prompt template based on format
- When `output_format="json"`:
  - Uses JSON-specific prompt from `prompts/anime_rag.py`
  - Extracts the "answer" field from the JSON response
  - Falls back to raw text if JSON parsing fails
- Improved content extraction logic to handle GPT-5 Responses API content blocks:
  - Filters out reasoning metadata blocks
  - Only keeps user-visible text blocks (types: None, "output_text", "text")
  - Properly handles both list and string content formats
  - Strips whitespace from final answer

### 2. Prompts (`prompts/anime_rag.py`)
- Added `ANIME_RAG_JSON_PROMPT` constant with JSON-specific system prompt
- Created `build_anime_rag_json_prompt()` function for JSON output
- JSON prompt includes the word "json" (required by OpenAI API when using `json_object` format)
- Instructs the model to structure response as JSON with an "answer" field
- Exported new function in `prompts/__init__.py`

### 3. App Context (`services/app_context.py`)
- Added `get_rag_chain(output_format: str)` method for dynamic format selection
- Maintains backward compatibility with cached `rag_chain` property (text format)
- Non-text formats bypass caching to allow format switching

### 4. CLI Commands (`cli/query.py` and `cli/repl.py`)
- Added `--output-format` flag with choices: ["text", "json"]
- Default: "text" (maintains existing behavior)
- JSON mode outputs structured data:
  ```json
  {
    "question": "user question",
    "answer": "AI response",
    "context": [  // optional, with --show-context
      {
        "title": "Anime Title",
        "anime_id": 123,
        "year": 2020,
        "episodes": 12
      }
    ]
  }
  ```
- JSON mode disables rich formatting for clean programmatic output
- Uses standard `input()` instead of rich console input in JSON mode

## Usage Examples

### Text Output (Default)
```bash
poetry run shokobot query -q "Recommend a sci-fi anime"
poetry run shokobot repl
```

### JSON Output
```bash
# Single question
poetry run shokobot query -q "Recommend a sci-fi anime" --output-format json

# With context
poetry run shokobot query -q "Recommend a sci-fi anime" --output-format json --show-context

# Interactive mode
poetry run shokobot repl --output-format json

# From file
poetry run shokobot query -f questions.txt --output-format json

# From stdin
echo "Recommend a sci-fi anime" | poetry run shokobot query --stdin --output-format json
```

### Programmatic Usage
```python
import subprocess
import json

result = subprocess.run(
    ["poetry", "run", "shokobot", "query", "-q", "Recommend a sci-fi anime", "--output-format", "json"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
print(f"Answer: {data['answer']}")
```

## Technical Details

### Response Format Parameter
The `response_format={"type": "json_object"}` parameter (passed explicitly to `ChatOpenAI`) instructs the OpenAI API to return responses in valid JSON format.

**Important Requirements:**
- The prompt MUST contain the word "json" when using `json_object` format (OpenAI API requirement)
- We use `build_anime_rag_json_prompt()` which includes "json" in the system prompt
- The response is automatically parsed to extract the "answer" field
- If JSON parsing fails, the raw text is used as fallback

This is particularly useful when:
- Integrating with other services that expect structured data
- Building APIs or microservices on top of ShokoBot
- Automating batch processing of queries
- Parsing and storing responses in databases

### Content Block Filtering
The improved content extraction handles GPT-5's response structure:
- **Reasoning blocks**: Filtered out (internal model reasoning)
- **Text blocks**: Extracted (user-visible content)
- **Output text blocks**: Extracted (formatted output)
- **String content**: Handled as fallback for simpler responses

This ensures clean, user-facing text regardless of the model's internal processing.

## Backward Compatibility
All changes are backward compatible:
- Default behavior unchanged (text output)
- Existing commands work without modification
- Cached RAG chain still used for default text format
- No breaking changes to existing APIs

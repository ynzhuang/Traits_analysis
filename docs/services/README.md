# Services Layer

This directory contains the service layer that abstracts common LangChain functionality used across the criteria analyzer project. The services provide a clean, reusable interface for LLM operations while maintaining consistency and reducing code duplication.

## Architecture Overview

The service layer follows a modular design with each service handling a specific aspect of LangChain operations:

```
services/
├── __init__.py              # Package initialization and exports
├── api_key_service.py       # API key management
├── cache_service.py         # LangChain caching
├── llm_service.py          # Language model initialization
├── prompt_service.py       # Prompt template processing
├── chain_service.py        # Chain creation and invocation
└── README.md               # This documentation
```

## Services

### APIKeyService

Manages API keys and configuration loading from JSON files.

**Key Features:**
- Load API keys from JSON files with error handling
- Validate required API keys are present
- Add model overrides for specific providers

**Usage:**
```python
from services.api_key_service import APIKeyService

# Load API keys
api_keys = APIKeyService.load_api_keys('api_keys.json')

# Add model override
api_keys = APIKeyService.add_model_override(api_keys, 'openai', 'gpt-4-turbo')

# Validate required keys
is_valid = APIKeyService.validate_api_keys(api_keys, ['openai', 'claude'])
```

### CacheService

Manages LangChain caching configuration.

**Key Features:**
- Enable/disable SQLite caching
- Configure cache database path
- Clear cache when needed

**Usage:**
```python
from services.cache_service import CacheService

# Enable caching
CacheService.setup_cache(enable_cache=True, database_path=".langchain.db")

# Disable caching
CacheService.setup_cache(enable_cache=False)

# Clear cache
CacheService.clear_cache()
```

### LLMService

Factory service for creating language model instances with structured output.

**Key Features:**
- Support for OpenAI, Google Gemini, and Anthropic Claude
- Provider-specific configuration handling
- Structured output integration
- Default model management

**Usage:**
```python
from services.llm_service import LLMService
from pydantic import BaseModel

class MyOutput(BaseModel):
    result: str

# Get LLM instance
llm, model_name = LLMService.get_llm('openai', api_keys, MyOutput)

# Check supported providers
providers = LLMService.get_supported_providers()  # ['openai', 'gemini', 'claude']
```

### PromptService

Handles prompt template loading, processing, and formatting.

**Key Features:**
- Load templates from files
- Escape curly braces for LangChain compatibility
- Provider-specific prompt formatting (Claude cache control)
- Template variable management

**Usage:**
```python
from services.prompt_service import PromptService

# Load template
template = PromptService.load_prompt_template('prompt.md')

# Create provider-specific prompt
prompt = PromptService.prepare_prompt_for_provider(
    template, 
    'claude', 
    "Human message: {input}",
    template_variables=['input']
)
```

### ChainService

Manages chain creation and invocation with error handling and retry logic.

**Key Features:**
- Simple chain creation (prompt | llm)
- Retry logic with exponential backoff
- Timing and performance monitoring
- Batch processing support

**Usage:**
```python
from services.chain_service import ChainService

# Create chain
chain = ChainService.create_chain(prompt, llm)

# Invoke with timing
result, duration = ChainService.invoke_chain_with_timing(
    chain, 
    {"input": "test"},
    "My operation"
)

# Invoke with retry logic
result = ChainService.invoke_chain(
    chain, 
    {"input": "test"},
    retry_count=3,
    retry_delay=1.0
)
```

## Migration Guide

### Before (Original Code)

```python
# Old way - duplicated across files
def get_api_keys(api_keys_file):
    with open(api_keys_file, 'r') as f:
        return json.load(f)

def get_llm(provider_name, api_keys):
    # 40+ lines of provider mapping and configuration
    # Duplicated in multiple files
    pass

# Manual prompt escaping
escaped_prompt = prompt_template.replace("{", "{{").replace("}", "}}")
prompt = ChatPromptTemplate.from_messages([...])

# Manual chain creation and invocation
chain = prompt | llm
result = chain.invoke(input_data)
```

### After (Service Layer)

```python
# New way - clean and reusable
from services import APIKeyService, LLMService, PromptService, ChainService

# Load configuration
api_keys = APIKeyService.load_api_keys(args.api_keys)
llm, model_name = LLMService.get_llm(args.model, api_keys, OutputModel)

# Create prompt
prompt = PromptService.prepare_prompt_for_provider(
    template, args.model, human_template, ['variable1', 'variable2']
)

# Execute
chain = ChainService.create_chain(prompt, llm)
result, duration = ChainService.invoke_chain_with_timing(chain, input_data)
```

## Benefits

1. **DRY Principle**: Eliminates ~200 lines of duplicated code
2. **Maintainability**: Single source of truth for LLM configurations
3. **Testability**: Each service can be unit tested independently
4. **Consistency**: Ensures same behavior across all scripts
5. **Extensibility**: Easy to add new providers or modify configurations
6. **Error Handling**: Centralized error handling and retry logic
7. **Performance**: Built-in timing and monitoring capabilities

## Configuration

The services use the same configuration format as the original scripts:

### API Keys JSON Format
```json
{
  "openai": "sk-...",
  "claude": "sk-ant-...",
  "gemini": "AI...",
  "openai_model": "gpt-4o",
  "claude_model": "claude-sonnet-4-20250514"
}
```

### Supported Providers
- **OpenAI**: `openai` (default: gpt-4o)
- **Google Gemini**: `gemini` (default: gemini-2.5-pro)
- **Anthropic Claude**: `claude` (default: claude-sonnet-4-20250514)

## Error Handling

All services include comprehensive error handling:

- **FileNotFoundError**: When configuration files are missing
- **ValueError**: For invalid provider names or configurations
- **JSONDecodeError**: For malformed configuration files
- **LLM Errors**: Automatic retry with exponential backoff

## Future Enhancements

The service layer is designed to be extensible:

1. **New Providers**: Add support for additional LLM providers
2. **Advanced Caching**: Support for Redis or other cache backends
3. **Monitoring**: Integration with monitoring and observability tools
4. **Configuration**: Support for YAML, TOML, or environment variables
5. **Async Support**: Asynchronous chain execution for better performance
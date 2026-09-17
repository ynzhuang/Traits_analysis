# LangSmith Integration Setup Guide

This guide explains how to set up and use LangSmith for debugging and tracing your criteria analyzer LLM operations.

## What is LangSmith?

LangSmith is a debugging and observability platform for LLM applications that provides:
- **Automatic tracing** of LangChain operations
- **Performance monitoring** with timing and token usage
- **Error tracking** and debugging capabilities
- **Input/output logging** for all LLM calls
- **Cost tracking** across different providers
- **Collaborative debugging** with team members

## Setup Instructions

### 1. Install Dependencies

The required dependencies are already added to `requirements.txt`. Install them:

```bash
pip install -r requirements.txt
```

### 2. Get LangSmith API Key

1. Sign up for a free account at [LangSmith](https://smith.langchain.com/)
2. Navigate to Settings → API Keys
3. Create a new API key
4. Copy the API key (starts with `ls_...`)

### 3. Configure API Keys

Add your LangSmith configuration to your `api_keys.json` file:

```json
{
  "openai": {
    "api-key": "your-openai-key",
    "model": "gpt-4o"
  },
  "claude": {
    "api-key": "your-claude-key", 
    "model": "claude-sonnet-4-20250514"
  },
  "langsmith": {
    "api-key": "ls_your_langsmith_api_key_here",
    "project": "criteria-analyzer",
    "endpoint": "https://api.smith.langchain.com"
  }
}
```

### 4. Test the Integration

Run the demo script to verify everything is working:

```bash
python demo/langsmith_demo.py
```

You should see output like:
```
✅ LangSmith tracing configured successfully!
✅ Initialized claude model: claude-sonnet-4-20250514
🔄 Running criteria analysis with LangSmith tracing...
✅ Analysis completed in 2.34 seconds
🔍 Check your LangSmith dashboard for detailed traces
```

## Features Enabled

### Automatic Tracing

All LangChain operations are automatically traced when LangSmith is configured:

- **LLM calls** with input/output logging
- **Chain executions** with timing information
- **Retry attempts** and error handling
- **Token usage** and cost tracking

### Enhanced Debugging

The integration provides enhanced debugging for common issues:

1. **Token Limit Errors**
   - Automatic detection of token limit issues
   - Input/output size logging
   - Suggested solutions

2. **Provider-Specific Errors**
   - Detailed error categorization
   - Provider-specific error handling
   - Retry logic with exponential backoff

3. **Performance Monitoring**
   - Request/response timing
   - Token usage estimation
   - Cost tracking per operation

### Manual Tracing

You can also add manual tracing for custom operations:

```python
from services.langsmith_service import LangSmithService

# Manual tracing context
with LangSmithService.trace_context("Custom Operation", {"param": "value"}) as trace:
    # Your custom logic here
    result = some_operation()
    
    # Update trace with results
    if trace:
        trace.outputs.update({"result": result})
```

## Viewing Traces

1. Go to [LangSmith Dashboard](https://smith.langchain.com/)
2. Select your project (default: "criteria-analyzer")
3. View traces in real-time as they execute
4. Click on individual traces to see detailed information:
   - Input/output data
   - Timing information
   - Error details
   - Token usage
   - Cost breakdown

## Configuration Options

### Environment Variables

LangSmith can also be configured via environment variables:

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=ls_your_api_key_here
export LANGSMITH_PROJECT=criteria-analyzer
export LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

### Project Organization

You can organize traces by project:

```python
# In your api_keys.json
"langsmith": {
    "api-key": "ls_...",
    "project": "criteria-analyzer-dev",  # Different project for development
    "endpoint": "https://api.smith.langchain.com"
}
```

### Disabling Tracing

To temporarily disable tracing without removing configuration:

```python
LangSmithService.configure_tracing(api_keys, enable_tracing=False)
```

## Troubleshooting

### Common Issues

1. **"LangSmith API key not found"**
   - Verify your `api_keys.json` contains the langsmith section
   - Check that the API key starts with `ls_`

2. **"LangSmith SDK not installed"**
   - Run `pip install langsmith`
   - Verify installation with `python -c "import langsmith"`

3. **Traces not appearing in dashboard**
   - Check your API key is correct
   - Verify the project name matches
   - Ensure `LANGSMITH_TRACING=true` is set

4. **Network connectivity issues**
   - Check firewall settings
   - Verify endpoint URL is correct
   - Try with different network connection

### Debug Information

Use the debug logging to troubleshoot:

```python
LangSmithService.log_debug_info()
```

This will output current configuration status.

## Best Practices

1. **Use descriptive operation names** for better trace organization
2. **Include relevant metadata** in trace contexts
3. **Monitor token usage** to optimize costs
4. **Review error patterns** to improve reliability
5. **Use different projects** for development vs production
6. **Share traces with team members** for collaborative debugging

## Integration with Existing Code

The LangSmith integration is designed to be non-intrusive:

- **Automatic activation** when API keys are configured
- **Graceful degradation** when LangSmith is unavailable
- **No code changes required** for basic tracing
- **Optional manual tracing** for custom operations

All existing functionality continues to work exactly as before, with the added benefit of comprehensive observability.
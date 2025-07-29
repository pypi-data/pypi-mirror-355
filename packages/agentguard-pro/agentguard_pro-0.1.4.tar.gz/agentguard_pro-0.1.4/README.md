# AgentGuard Python SDK

The official Python SDK for [AgentGuard Pro](https://agentguardpro.com) - Enterprise AI governance and compliance platform.

## 🚀 One-Line Integration

Transform your AI infrastructure with a single line of code:

```python
from agentguard import AgentGuard

# Initialize once
agentguard = AgentGuard(tenant_id="your-tenant")

# Before: Complex manual compliance
response = openai.ChatCompletion.create(model="gpt-4", messages=[...])

# After: Automatic compliance with intercept()
response = agentguard.intercept(
    openai.ChatCompletion.create,
    model="gpt-4",
    messages=[...]
)
```

That's it! The `intercept()` method automatically handles:
- ✅ Authorization checks
- ✅ Provider detection
- ✅ Context extraction
- ✅ Audit logging
- ✅ Error handling

## Installation

```bash
pip install agentguard
```

## Quick Start

### 1. Set up your environment

```bash
export AGENTGUARD_API_KEY="your-api-key"
export AGENTGUARD_TENANT_ID="your-tenant-id"
```

### 2. Use with any AI provider

```python
from agentguard import AgentGuard
import openai

# Initialize AgentGuard
agentguard = AgentGuard()

# Intercept any AI call
response = agentguard.intercept(
    openai.ChatCompletion.create,
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)
```

## Supported Providers

The SDK automatically detects and supports:
- ✅ OpenAI (GPT-4, GPT-3.5, DALL-E, etc.)
- ✅ Anthropic (Claude)
- ✅ Azure OpenAI
- ✅ Custom providers (via registration)

## Advanced Usage

### Custom Provider Registration

```python
# Register your custom AI provider
agentguard.register_provider(
    name='custom-llm',
    detect_fn=lambda fn, args, kwargs: 'custom' in str(fn),
    extract_model_fn=lambda fn, args, kwargs: kwargs.get('model', 'custom'),
    extract_context_fn=lambda fn, args, kwargs: {'custom': True},
    resource='ai:custom'
)

# Now intercept() works with your custom provider!
response = agentguard.intercept(custom_llm.generate, prompt="Hello")
```

### Error Handling

```python
from agentguard import AgentGuardError

try:
    response = agentguard.intercept(
        openai.ChatCompletion.create,
        model="gpt-4",
        messages=[{"role": "user", "content": "Sensitive request"}]
    )
except AgentGuardError as e:
    if e.code == 'AGENTGUARD_ACCESS_DENIED':
        print(f"Access denied: {e}")
        # Handle authorization failure
```

### Direct Authorization (Advanced)

```python
# For fine-grained control, use authorize() directly
auth_result = agentguard.authorize(
    subject="user@example.com",
    resource="ai:gpt-4",
    action="generate",
    context={"purpose": "customer_support"}
)

if auth_result['allowed']:
    # Proceed with AI call
    pass
```

## Legacy Context Manager (Deprecated)

The SDK still supports the legacy context manager pattern:

```python
from agentguard import protect

with protect(context={"user_id": "123"}) as guard:
    response = openai.ChatCompletion.create(...)
    guard.complete(response)
```


## Configuration

### Environment Variables

- `AGENTGUARD_API_KEY`: Your API key (required)
- `AGENTGUARD_TENANT_ID`: Default tenant ID
- `AGENTGUARD_PRINCIPAL`: Default principal/user
- `AGENTGUARD_BASE_URL`: API base URL (defaults to https://api.agentguard.pro)

### Initialization Options

```python
agentguard = AgentGuard(
    api_key="your-api-key",      # Or use env var
    tenant_id="your-tenant",      # Or use env var
    principal="user@example.com", # Or use env var
    base_url="https://custom.api" # Or use env var
)
```

## Examples

See the [examples/](examples/) directory for complete examples:
- [intercept_demo.py](examples/intercept_demo.py) - Basic intercept() usage
- [openai_integration.py](examples/openai_integration.py) - OpenAI integration
- More examples coming soon!

## Support

- 📧 Email: support@agentguard.pro
- 📚 Documentation: https://docs.agentguardpro.com
- 💬 Discord: https://discord.gg/agentguard



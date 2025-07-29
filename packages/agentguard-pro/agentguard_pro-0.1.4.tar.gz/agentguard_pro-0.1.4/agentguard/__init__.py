"""
AgentGuard Pro Python SDK
-------------------------

A client library for interacting with the AgentGuard Pro gateway.

This package provides a simple way to protect AI agent calls
with policy enforcement and audit trails.

Basic usage:

    from agentguard import AgentGuard
    
    # Initialize the client
    agentguard = AgentGuard(tenant_id="my-tenant")
    
    # Use the intercept method for one-line integration
    response = agentguard.intercept(
        openai.ChatCompletion.create,
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )

Legacy usage (context manager):

    from agentguard import protect

    with protect(context={"user_id": "123"}) as guard:
        # Make your AI API calls here
        response = openai.Completion.create(
            model="gpt-4",
            prompt="Generate a response that complies with my policies"
        )
        
        # Optionally mark as completed with the response
        guard.complete(response)
"""

__version__ = "0.2.0"

from .protect import protect, AgentGuardContext
from .client import AgentGuard, AgentGuardError

__all__ = ["protect", "AgentGuardContext", "AgentGuard", "AgentGuardError"]
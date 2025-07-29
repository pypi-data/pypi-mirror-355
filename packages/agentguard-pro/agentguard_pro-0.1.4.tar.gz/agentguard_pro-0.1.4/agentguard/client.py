"""
AgentGuard Python SDK Client
"""

import os
import time
import json
import inspect
import asyncio
import functools
from typing import Any, Dict, Optional, Callable, TypeVar, Union, AsyncIterator
from datetime import datetime, timezone
import requests
import logging

logger = logging.getLogger("agentguard")

T = TypeVar('T')


class AgentGuard:
    """AgentGuard Python SDK Client with intercept() method support."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        tenant_id: Optional[str] = None,
        principal: Optional[str] = None
    ):
        """
        Initialize the AgentGuard client.
        
        Args:
            api_key: API key for authentication (defaults to AGENTGUARD_API_KEY env var)
            base_url: Base URL for the API (defaults to https://api.agentguard.pro)
            tenant_id: Default tenant ID for all requests
            principal: Default principal/user for all requests
        """
        self.api_key = api_key or os.environ.get('AGENTGUARD_API_KEY')
        if not self.api_key:
            raise ValueError("API key is required. Set AGENTGUARD_API_KEY or pass api_key parameter.")
        
        self.base_url = (base_url or os.environ.get('AGENTGUARD_BASE_URL', 'https://api.agentguard.pro')).rstrip('/')
        self.tenant_id = tenant_id or os.environ.get('AGENTGUARD_TENANT_ID')
        self.principal = principal or os.environ.get('AGENTGUARD_PRINCIPAL', 'default-user')
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        # Provider registry for auto-detection
        self.provider_registry = ProviderRegistry()
        self._register_default_providers()
    
    def _register_default_providers(self):
        """Register default AI providers."""
        # OpenAI
        self.provider_registry.register(
            'openai',
            lambda fn, args, kwargs: hasattr(fn, '__module__') and 'openai' in str(fn.__module__),
            lambda fn, args, kwargs: (
                kwargs.get('model') or 
                (args[0].get('model') if args and isinstance(args[0], dict) else None) or 
                'unknown'
            ),
            lambda fn, args, kwargs: {
                **(args[0] if args and isinstance(args[0], dict) else {}),
                **kwargs
            },
            'ai:openai'
        )
        
        # Anthropic
        self.provider_registry.register(
            'anthropic',
            lambda fn, args, kwargs: hasattr(fn, '__module__') and 'anthropic' in str(fn.__module__),
            lambda fn, args, kwargs: (
                kwargs.get('model') or 
                (args[0].get('model') if args and isinstance(args[0], dict) else None) or 
                'unknown'
            ),
            lambda fn, args, kwargs: {
                **(args[0] if args and isinstance(args[0], dict) else {}),
                **kwargs
            },
            'ai:anthropic'
        )
    
    def authorize(self, subject: str, resource: str, action: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check if an action is authorized.
        
        Args:
            subject: The subject (user/principal) requesting access
            resource: The resource being accessed
            action: The action being performed
            context: Additional context for the authorization decision
            
        Returns:
            Authorization result with 'allowed' boolean and optional 'reason'
        """
        response = self.session.post(
            f'{self.base_url}/v1/authorize',
            json={
                'subject': subject,
                'resource': resource,
                'action': action,
                'context': context or {}
            }
        )
        response.raise_for_status()
        return response.json()
    
    def intercept(self, ai_function: Callable[..., T], *args, **kwargs) -> T:
        """
        Intercept and authorize an AI function call.
        
        This method wraps any AI function call with automatic authorization,
        audit logging, and error handling.
        
        Args:
            ai_function: The AI function to intercept (e.g., openai.ChatCompletion.create)
            *args: Arguments to pass to the AI function
            **kwargs: Keyword arguments to pass to the AI function
            
        Returns:
            The result of the AI function call
            
        Raises:
            AgentGuardError: If authorization is denied
            
        Example:
            # Instead of:
            response = openai.ChatCompletion.create(model="gpt-4", messages=[...])
            
            # Use:
            response = agentguard.intercept(
                openai.ChatCompletion.create,
                model="gpt-4",
                messages=[...]
            )
        """
        # Detect provider and extract context
        provider_info = self.provider_registry.detect(ai_function, args, kwargs)
        if not provider_info:
            logger.warning('AgentGuard: Could not detect AI provider, using generic authorization')
        
        # Extract model and context
        model = provider_info.extract_model(ai_function, args, kwargs) if provider_info else 'unknown'
        extracted_context = provider_info.extract_context(ai_function, args, kwargs) if provider_info else {}
        
        # Build resource string
        resource = provider_info.resource if provider_info else f'ai:{model}'
        
        # Get tenant ID and principal
        tenant_id = self.tenant_id
        principal = self.principal
        
        if not tenant_id:
            raise ValueError('AgentGuard: tenantId is required. Set it in the constructor or AGENTGUARD_TENANT_ID env var')
        
        # Authorize the action
        auth_start = time.time()
        auth_result = self.authorize(
            subject=principal,
            resource=resource,
            action='generate',
            context={
                'tenant_id': tenant_id,
                'provider': provider_info.name if provider_info else 'unknown',
                'model': model,
                'intercepted': True,
                'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                **extracted_context
            }
        )
        auth_duration = time.time() - auth_start
        
        if not auth_result.get('allowed', False):
            error = AgentGuardError(f"AgentGuard: Access denied - {auth_result.get('reason', 'Unauthorized')}")
            error.code = 'AGENTGUARD_ACCESS_DENIED'
            error.auth_result = auth_result
            raise error
        
        # Execute the AI function
        exec_start = time.time()
        try:
            # Handle both sync and async functions
            if asyncio.iscoroutinefunction(ai_function):
                result = asyncio.run(ai_function(*args, **kwargs))
            else:
                result = ai_function(*args, **kwargs)
            
            exec_duration = time.time() - exec_start
            
            # Log completion asynchronously (fire and forget)
            self._log_completion_async(
                resource=resource,
                model=model,
                duration=exec_duration * 1000,  # Convert to ms
                success=True,
                event_id=auth_result.get('eventId', 'unknown')
            )
            
            return result
            
        except Exception as e:
            exec_duration = time.time() - exec_start
            
            # Log failure asynchronously
            self._log_completion_async(
                resource=resource,
                model=model,
                duration=exec_duration * 1000,
                success=False,
                error=str(e),
                event_id=auth_result.get('eventId', 'unknown')
            )
            
            raise
    
    def _log_completion_async(self, **kwargs):
        """Log completion event asynchronously."""
        try:
            # Fire and forget - don't wait for response
            self.session.post(
                f'{self.base_url}/v1/events/completion',
                json=kwargs,
                timeout=1.0  # Short timeout
            )
        except:
            # Ignore logging errors
            pass
    
    def register_provider(
        self,
        name: str,
        detect_fn: Callable[[Callable, tuple, dict], bool],
        extract_model_fn: Callable[[Callable, tuple, dict], str],
        extract_context_fn: Callable[[Callable, tuple, dict], Dict[str, Any]],
        resource: str
    ):
        """
        Register a custom AI provider for automatic detection.
        
        Args:
            name: Name of the provider
            detect_fn: Function to detect if a call is from this provider
            extract_model_fn: Function to extract the model name
            extract_context_fn: Function to extract additional context
            resource: Resource string for this provider
        """
        self.provider_registry.register(name, detect_fn, extract_model_fn, extract_context_fn, resource)


class ProviderInfo:
    """Information about a detected AI provider."""
    
    def __init__(self, name: str, extract_model: Callable, extract_context: Callable, resource: str):
        self.name = name
        self.extract_model = extract_model
        self.extract_context = extract_context
        self.resource = resource


class ProviderRegistry:
    """Registry for AI provider detection."""
    
    def __init__(self):
        self.providers = []
    
    def register(
        self,
        name: str,
        detect_fn: Callable[[Callable, tuple, dict], bool],
        extract_model_fn: Callable[[Callable, tuple, dict], str],
        extract_context_fn: Callable[[Callable, tuple, dict], Dict[str, Any]],
        resource: str
    ):
        """Register a provider."""
        self.providers.append({
            'name': name,
            'detect': detect_fn,
            'extract_model': extract_model_fn,
            'extract_context': extract_context_fn,
            'resource': resource
        })
    
    def detect(self, ai_function: Callable, args: tuple, kwargs: dict) -> Optional[ProviderInfo]:
        """Detect which provider a function belongs to."""
        for provider in self.providers:
            try:
                if provider['detect'](ai_function, args, kwargs):
                    return ProviderInfo(
                        name=provider['name'],
                        extract_model=lambda fn, a, k: provider['extract_model'](fn, a, k),
                        extract_context=lambda fn, a, k: provider['extract_context'](fn, a, k),
                        resource=provider['resource']
                    )
            except:
                continue
        return None


class AgentGuardError(Exception):
    """AgentGuard specific error."""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.code = None
        self.auth_result = None

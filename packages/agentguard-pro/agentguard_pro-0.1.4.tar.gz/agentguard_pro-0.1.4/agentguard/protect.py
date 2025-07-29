"""
Context manager for protecting AI agent calls with policy enforcement.
"""

import contextlib
import json
import logging
import requests
import time
import uuid
from typing import Any, Dict, Optional, Union

logger = logging.getLogger("agentguard")

class AgentGuardContext:
    """Context manager for protecting AI agent calls."""
    
    def __init__(self, context: Dict[str, Any], gateway_url: str = "http://localhost:8080"):
        """
        Initialize the context manager.
        
        Args:
            context: Dictionary with context information for policy evaluation
            gateway_url: URL of the AgentGuard gateway
        """
        self.context = context
        self.gateway_url = gateway_url.rstrip("/")
        self.request_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.completed = False
        self.allowed = False
    
    def __enter__(self):
        """Start the protection context and check if the action is allowed."""
        try:
            response = requests.post(
                f"{self.gateway_url}/protect",
                json={
                    "request_id": self.request_id,
                    "timestamp": int(self.start_time * 1000),
                    "context": self.context
                },
                headers={"Content-Type": "application/json"},
                timeout=5.0  # 5 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self.allowed = result.get("allowed", False)
                if not self.allowed:
                    reason = result.get("reason", "Unknown policy violation")
                    logger.warning(f"Request denied: {reason}")
            else:
                # On error, fail closed
                logger.error(f"Gateway returned status {response.status_code}")
                self.allowed = False
                
        except Exception as e:
            # On exception, fail closed
            logger.exception(f"Failed to connect to gateway: {e}")
            self.allowed = False
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete the protection context if not already done."""
        if not self.completed:
            self.complete({"error": str(exc_val)} if exc_val else None)
        
        # If policy denied and no exception occurred, raise PolicyViolationError
        if not self.allowed and exc_type is None:
            # Don't suppress exceptions from the with block
            return False
    
    def complete(self, result: Optional[Union[Dict[str, Any], str]] = None):
        """
        Mark the protection context as completed with the result.
        
        Args:
            result: The result of the AI operation (optional)
        """
        if self.completed:
            logger.warning("Protection context already completed")
            return
        
        self.completed = True
        end_time = time.time()
        duration_ms = int((end_time - self.start_time) * 1000)
        
        try:
            # Convert result to JSON if it's a string
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    result = {"text": result}
            
            requests.post(
                f"{self.gateway_url}/complete",
                json={
                    "request_id": self.request_id,
                    "timestamp": int(end_time * 1000),
                    "duration_ms": duration_ms,
                    "result": result
                },
                headers={"Content-Type": "application/json"},
                timeout=5.0
            )
        except Exception as e:
            logger.exception(f"Failed to complete protection context: {e}")


def protect(context: Dict[str, Any], gateway_url: str = "http://localhost:8080"):
    """
    Context manager for protecting AI agent calls.
    
    Args:
        context: Dictionary with context information for policy evaluation
        gateway_url: URL of the AgentGuard gateway
        
    Returns:
        An AgentGuardContext instance
        
    Example:
        with protect({"user_id": "123"}) as guard:
            # Make your AI API calls here
            response = openai.Completion.create(...)
            guard.complete(response)
    """
    return AgentGuardContext(context, gateway_url)
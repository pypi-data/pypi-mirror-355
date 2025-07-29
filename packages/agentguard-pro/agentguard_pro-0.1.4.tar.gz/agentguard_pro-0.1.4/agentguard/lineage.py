"""
Agent Lineage Tracking Module for AgentGuard SDK
"""
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentLineageTracker:
    """Tracks agent lineage and relationships"""
    
    def __init__(self, gateway_url: str, api_key: str):
        self.gateway_url = gateway_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_lineage(self, 
                      parent_agent_id: str,
                      child_agent_id: str,
                      tenant_id: str,
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a parent-child relationship between agents"""
        payload = {
            "parent_agent_id": parent_agent_id,
            "child_agent_id": child_agent_id,
            "tenant_id": tenant_id,
            "metadata": metadata or {}
        }
        
        response = requests.post(
            f"{self.gateway_url}/v1/agent-lineage/lineage",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def send_message(self,
                    from_agent_id: str,
                    from_session_id: str,
                    to_agent_id: str,
                    to_session_id: str,
                    tenant_id: str,
                    message_type: str,
                    content: Dict[str, Any],
                    priority: str = "normal") -> Dict[str, Any]:
        """Send a message between agents"""
        payload = {
            "from_agent_id": from_agent_id,
            "from_session_id": from_session_id,
            "to_agent_id": to_agent_id,
            "to_session_id": to_session_id,
            "tenant_id": tenant_id,
            "message_type": message_type,
            "content": content,
            "priority": priority
        }
        
        response = requests.post(
            f"{self.gateway_url}/v1/agent-lineage/messages",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def join_collaboration(self,
                          agent_id: str,
                          session_id: str,
                          collaboration_id: str,
                          tenant_id: str,
                          role: str = "participant") -> Dict[str, Any]:
        """Join an agent to a collaboration"""
        payload = {
            "agent_id": agent_id,
            "session_id": session_id,
            "collaboration_id": collaboration_id,
            "tenant_id": tenant_id,
            "role": role
        }
        
        response = requests.post(
            f"{self.gateway_url}/v1/agent-lineage/collaborations/join",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_agent_network(self, agent_id: str) -> Dict[str, Any]:
        """Get the collaboration network for an agent"""
        response = requests.get(
            f"{self.gateway_url}/v1/agent-lineage/agents/{agent_id}/network",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_ancestors(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all ancestors of an agent"""
        response = requests.get(
            f"{self.gateway_url}/v1/agent-lineage/agents/{agent_id}/ancestors",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_descendants(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all descendants of an agent"""
        response = requests.get(
            f"{self.gateway_url}/v1/agent-lineage/agents/{agent_id}/descendants",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


# Example usage in multi-agent system
class MultiAgentOrchestrator:
    """Example orchestrator using lineage tracking"""
    
    def __init__(self, gateway_url: str, api_key: str):
        self.lineage = AgentLineageTracker(gateway_url, api_key)
        self.tenant_id = "your-tenant-id"
    
    def spawn_worker_agent(self, parent_id: str, parent_session: str, 
                          worker_id: str, worker_session: str, task: Dict[str, Any]):
        """Spawn a worker agent and track lineage"""
        # Create lineage relationship
        lineage = self.lineage.create_lineage(
            parent_agent_id=parent_id,
            child_agent_id=worker_id,
            tenant_id=self.tenant_id,
            metadata={
                "spawn_reason": "task_delegation",
                "task_type": task.get("type"),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Send task to worker
        message = self.lineage.send_message(
            from_agent_id=parent_id,
            from_session_id=parent_session,
            to_agent_id=worker_id,
            to_session_id=worker_session,
            tenant_id=self.tenant_id,
            message_type="task_assignment",
            content=task,
            priority="high"
        )
        
        logger.info(f"Spawned worker {worker_id} with lineage {lineage['id']}")
        return lineage, message

"""
Local Services Backend - Services running locally on the same machine.
Examples: Ollama, Local model servers
"""

import aiohttp
import json
from typing import Dict, Any, List, Optional
from .base_backend_client import BaseBackendClient


class OllamaBackendClient(BaseBackendClient):
    """Pure connection client for local Ollama service"""
    
    def __init__(self, host: str = "localhost", port: int = 11434):
        self.base_url = f"http://{host}:{port}"
        self._session = None
        
    async def _get_session(self):
        """Get or create HTTP session"""
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self._session
        
    async def post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to Ollama API"""
        session = await self._get_session()
        async with session.post(f"{self.base_url}{endpoint}", json=payload) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """Make GET request to Ollama API"""
        session = await self._get_session()
        async with session.get(f"{self.base_url}{endpoint}") as response:
            response.raise_for_status()
            return await response.json()
    
    async def health_check(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            await self.get("/api/tags")
            return True
        except Exception:
            return False
            
    async def close(self):
        """Close the HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None


class LocalModelServerClient(BaseBackendClient):
    """Generic client for local model servers"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    async def generate_completion(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate completion using generic local server"""
        # Implementation depends on local server API
        raise NotImplementedError("Implement based on your local server API")
    
    async def health_check(self) -> bool:
        """Check if local server is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False 
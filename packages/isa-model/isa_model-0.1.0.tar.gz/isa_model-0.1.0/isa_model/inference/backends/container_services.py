"""
Container Services Backend - Docker/K8s deployed services.
Examples: Triton Inference Server, vLLM, TensorFlow Serving
"""

import aiohttp
import json
from typing import Dict, Any, List, Optional
from .base_backend_client import BaseBackendClient
from .triton_client import TritonBackendClient  # Re-export existing Triton client


class VLLMBackendClient(BaseBackendClient):
    """Pure connection client for vLLM service deployed in containers"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        self._session = None
    
    async def _get_session(self):
        """Get or create HTTP session"""
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60))
        return self._session
    
    async def post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to vLLM API"""
        session = await self._get_session()
        async with session.post(f"{self.base_url}{endpoint}", json=payload, headers=self.headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """Make GET request to vLLM API"""
        session = await self._get_session()
        async with session.get(f"{self.base_url}{endpoint}", headers=self.headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def health_check(self) -> bool:
        """Check if vLLM service is healthy"""
        try:
            await self.get("/health")
            return True
        except Exception:
            return False
            
    async def close(self):
        """Close the HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None


class TensorFlowServingClient(BaseBackendClient):
    """Backend client for TensorFlow Serving in containers"""
    
    def __init__(self, base_url: str, model_name: str, version: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.version = version or "latest"
    
    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using TensorFlow Serving"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/v1/models/{self.model_name}"
            if self.version != "latest":
                url += f"/versions/{self.version}"
            url += ":predict"
            
            payload = {"instances": [inputs]}
            async with session.post(url, json=payload) as response:
                return await response.json()
    
    async def health_check(self) -> bool:
        """Check if TensorFlow Serving is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v1/models/{self.model_name}"
                async with session.get(url) as response:
                    return response.status == 200
        except Exception:
            return False


class KubernetesServiceClient(BaseBackendClient):
    """Generic client for services deployed in Kubernetes"""
    
    def __init__(self, service_url: str, namespace: str = "default"):
        self.service_url = service_url.rstrip('/')
        self.namespace = namespace
    
    async def health_check(self) -> bool:
        """Check if K8s service is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.service_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False 

import aiohttp
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from .base_backend_client import BaseBackendClient


class TritonBackendClient(BaseBackendClient):
    """Pure connection client for Triton Inference Server"""
    
    def __init__(self, url: str = "localhost:8000", protocol: str = "http"):
        self.base_url = f"http://{url}" if not url.startswith("http") else url
        self.protocol = protocol
        self._session = None
        
    async def _get_session(self):
        """Get or create HTTP session"""
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120))
        return self._session
        
    async def post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to Triton server"""
        session = await self._get_session()
        async with session.post(f"{self.base_url}{endpoint}", json=payload) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """Make GET request to Triton server"""
        session = await self._get_session()
        async with session.get(f"{self.base_url}{endpoint}") as response:
            response.raise_for_status()
            return await response.json()
            
    async def model_ready(self, model_name: str) -> bool:
        """Check if model is ready"""
        try:
            await self.get(f"/v2/models/{model_name}/ready")
            return True
        except Exception:
            return False
            
    async def model_metadata(self, model_name: str) -> Dict[str, Any]:
        """Get model metadata"""
        return await self.get(f"/v2/models/{model_name}")
        
    async def server_ready(self) -> bool:
        """Check if server is ready"""
        try:
            await self.get("/v2/health/ready")
            return True
        except Exception:
            return False
            
    async def health_check(self) -> bool:
        """Check server health"""
        return await self.server_ready()
        
    async def close(self):
        """Close the HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None


# Keep old class name for backward compatibility
class TritonClient(TritonBackendClient):
    """Backward compatibility alias"""
    
    def __init__(self, backend_connector_config: Dict = None, config: Dict = None):
        if backend_connector_config:
            url = backend_connector_config.get("url", "localhost:8000")
        else:
            url = "localhost:8000"
        super().__init__(url)
        
    async def infer(self, 
                    model_runtime_config: Dict, 
                    unified_request_payload: Dict, 
                    task_type: str, 
                    request_id: str) -> Dict:
        """Legacy method for backward compatibility"""
        # This is a placeholder for the old interface
        # New code should use the direct HTTP methods
        raise NotImplementedError("Use direct HTTP methods instead")
        
    async def stream(self, 
                     model_runtime_config: Dict, 
                     unified_request_payload: Dict, 
                     task_type: str, 
                     request_id: str) -> AsyncGenerator[Dict, None]:
        """Legacy method for backward compatibility"""
        # This is a placeholder for the old interface
        # New code should use the direct HTTP methods
        raise NotImplementedError("Use direct HTTP methods instead")
        yield  # Make it a generator
"""
Base backend client interface for all AI service backends.
Defines the common interface that all backend clients must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator, Optional


class BaseBackendClient(ABC):
    """Abstract base class for all backend clients"""
    
    def __init__(self, *args, **kwargs):
        """Initialize backend client"""
        pass
        
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the backend service is healthy"""
        pass
        
    async def close(self):
        """Close any open connections"""
        pass 

    
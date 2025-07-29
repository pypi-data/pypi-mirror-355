from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from isa_model.inference.base import ModelType, Capability

class BaseProvider(ABC):
    """Base class for all AI providers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    def get_capabilities(self) -> Dict[ModelType, List[Capability]]:
        """Get provider capabilities by model type"""
        pass
    
    @abstractmethod
    def get_models(self, model_type: ModelType) -> List[str]:
        """Get available models for given type"""
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration"""
        return self.config
    
    @abstractmethod
    def is_reasoning_model(self, model_name: str) -> bool:
        """Check if the model is optimized for reasoning tasks"""
        pass
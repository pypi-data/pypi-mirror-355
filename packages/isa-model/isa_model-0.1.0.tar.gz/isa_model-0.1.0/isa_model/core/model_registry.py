from typing import Dict, List, Optional, Any
from enum import Enum
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class ModelCapability(str, Enum):
    """Model capabilities"""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    EMBEDDING = "embedding"
    RERANKING = "reranking"
    REASONING = "reasoning"
    IMAGE_GENERATION = "image_generation"
    IMAGE_ANALYSIS = "image_analysis"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    IMAGE_UNDERSTANDING = "image_understanding"

class ModelType(str, Enum):
    """Model types"""
    LLM = "llm"
    EMBEDDING = "embedding"
    RERANK = "rerank"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    VISION = "vision"

class ModelRegistry:
    """Registry for model metadata and capabilities"""
    
    def __init__(self, registry_file: str = "./models/model_registry.json"):
        self.registry_file = Path(registry_file)
        self.registry: Dict[str, Dict[str, Any]] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load model registry from file"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                self.registry = json.load(f)
        else:
            self.registry = {}
            self._save_registry()
    
    def _save_registry(self):
        """Save model registry to file"""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def register_model(self, 
                      model_id: str,
                      model_type: ModelType,
                      capabilities: List[ModelCapability],
                      metadata: Dict[str, Any]) -> bool:
        """Register a model with its capabilities and metadata"""
        try:
            self.registry[model_id] = {
                "type": model_type,
                "capabilities": [cap.value for cap in capabilities],
                "metadata": metadata
            }
            self._save_registry()
            logger.info(f"Registered model {model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register model {model_id}: {e}")
            return False
    
    def unregister_model(self, model_id: str) -> bool:
        """Unregister a model"""
        try:
            if model_id in self.registry:
                del self.registry[model_id]
                self._save_registry()
                logger.info(f"Unregistered model {model_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister model {model_id}: {e}")
            return False
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model information"""
        return self.registry.get(model_id)
    
    def get_models_by_type(self, model_type: ModelType) -> Dict[str, Dict[str, Any]]:
        """Get all models of a specific type"""
        return {
            model_id: info
            for model_id, info in self.registry.items()
            if info["type"] == model_type
        }
    
    def get_models_by_capability(self, capability: ModelCapability) -> Dict[str, Dict[str, Any]]:
        """Get all models with a specific capability"""
        return {
            model_id: info
            for model_id, info in self.registry.items()
            if capability.value in info["capabilities"]
        }
    
    def has_capability(self, model_id: str, capability: ModelCapability) -> bool:
        """Check if a model has a specific capability"""
        model_info = self.get_model_info(model_id)
        if not model_info:
            return False
        return capability.value in model_info["capabilities"]
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all registered models"""
        return self.registry 
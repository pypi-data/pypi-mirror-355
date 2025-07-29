from isa_model.inference.providers.base_provider import BaseProvider
from isa_model.inference.base import ModelType, Capability
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class OllamaProvider(BaseProvider):
    """Provider for Ollama API"""
    
    def __init__(self, config=None):
        """
        Initialize the Ollama Provider
        
        Args:
            config (dict, optional): Configuration for the provider
                - base_url: Base URL for Ollama API (default: http://localhost:11434)
                - timeout: Timeout for API calls in seconds
        """
        default_config = {
            "base_url": "http://localhost:11434",
            "timeout": 60,
            "stream": True,
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048,
            "keep_alive": "5m"
        }
        
        # Merge default config with provided config
        merged_config = {**default_config, **(config or {})}
        
        super().__init__(config=merged_config)
        self.name = "ollama"
        
        logger.info(f"Initialized OllamaProvider with URL: {self.config['base_url']}")
    
    def get_capabilities(self) -> Dict[ModelType, List[Capability]]:
        """Get provider capabilities by model type"""
        return {
            ModelType.LLM: [
                Capability.CHAT, 
                Capability.COMPLETION
            ],
            ModelType.EMBEDDING: [
                Capability.EMBEDDING
            ],
            ModelType.VISION: [
                Capability.IMAGE_UNDERSTANDING
            ]
        }
    
    def get_models(self, model_type: ModelType) -> List[str]:
        """Get available models for given type"""
        # Placeholder: In real implementation, this would query Ollama API
        if model_type == ModelType.LLM:
            return ["llama3", "mistral", "phi3", "llama3.1", "codellama", "gemma"]
        elif model_type == ModelType.EMBEDDING:
            return ["bge-m3", "nomic-embed-text"]
        elif model_type == ModelType.VISION:
            return ["llava", "bakllava", "llama3-vision"]
        else:
            return []
    
    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration"""
        return self.config
    
    def is_reasoning_model(self, model_name: str) -> bool:
        """Check if the model is optimized for reasoning tasks"""
        # Default implementation: consider larger models as reasoning-capable
        reasoning_models = ["llama3.1", "llama3", "claude3", "gpt4", "mixtral", "gemma", "palm2"]
        return any(rm in model_name.lower() for rm in reasoning_models)
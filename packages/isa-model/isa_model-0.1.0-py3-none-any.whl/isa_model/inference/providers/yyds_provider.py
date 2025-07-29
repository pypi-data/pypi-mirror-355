from isa_model.inference.providers.base_provider import BaseProvider
from isa_model.inference.base import ModelType, Capability
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class YYDSProvider(BaseProvider):
    """Provider for YYDS API (Your YYDS Provider API)"""
    
    def __init__(self, config=None):
        """
        Initialize the YYDS Provider
        
        Args:
            config (dict, optional): Configuration for the provider
                - api_key: API key for authentication
                - api_base: Base URL for YYDS API
                - timeout: Timeout for API calls in seconds
        """
        default_config = {
            "api_base": "https://api.yyds.ai/v1",
            "timeout": 60,
            "max_retries": 3,
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048
        }
        
        # Merge default config with provided config
        merged_config = {**default_config, **(config or {})}
        
        super().__init__(config=merged_config)
        self.name = "yyds"
        
        # Validate API key
        api_key = self.config.get("api_key")
        if not api_key:
            logger.warning("No API key provided for YYDS Provider. Some operations may fail.")
        
        logger.info(f"Initialized YYDSProvider with API base: {self.config['api_base']}")
    
    def get_capabilities(self) -> Dict[ModelType, List[Capability]]:
        """Get provider capabilities by model type"""
        return {
            ModelType.LLM: [
                Capability.CHAT, 
                Capability.COMPLETION
            ],
            ModelType.VISION: [
                Capability.IMAGE_CLASSIFICATION,
                Capability.IMAGE_UNDERSTANDING
            ],
            ModelType.AUDIO: [
                Capability.SPEECH_TO_TEXT,
                Capability.TEXT_TO_SPEECH
            ]
        }
    
    def get_models(self, model_type: ModelType) -> List[str]:
        """Get available models for given type"""
        # Placeholder: In real implementation, this would query the YYDS API
        if model_type == ModelType.LLM:
            return ["yyds-l", "yyds-xl", "yyds-xxl"]
        elif model_type == ModelType.VISION:
            return ["yyds-vision", "yyds-multimodal"]
        elif model_type == ModelType.AUDIO:
            return ["yyds-speech", "yyds-tts"]
        else:
            return []
    
    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration"""
        # Return a copy of the config, without the API key for security
        config_copy = self.config.copy()
        if "api_key" in config_copy:
            config_copy["api_key"] = "***"  # Mask the API key
        return config_copy
    
    def is_reasoning_model(self, model_name: str) -> bool:
        """Check if the model is optimized for reasoning tasks"""
        # Only the largest models are considered reasoning-capable
        return model_name in ["yyds-xxl"]
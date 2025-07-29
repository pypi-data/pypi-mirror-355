import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union

from isa_model.inference.services.base_service import BaseService
from isa_model.inference.backends.triton_client import TritonClient

logger = logging.getLogger(__name__)


class LlamaService(BaseService):
    """
    Service for Llama LLM using Triton Inference Server.
    """
    
    def __init__(self, triton_url: str = "localhost:8001", model_name: str = "llama"):
        """
        Initialize the Llama service.
        
        Args:
            triton_url: URL of the Triton Inference Server
            model_name: Name of the model in Triton
        """
        super().__init__()
        self.triton_url = triton_url
        self.model_name = model_name
        self.client = None
        
        # Default generation config
        self.default_config = {
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 50,
            "repetition_penalty": 1.1,
            "do_sample": True
        }
        
        self.logger = logger
    
    async def load(self) -> None:
        """
        Load the client connection to Triton.
        """
        if self.is_loaded():
            return
        
        try:
            # Create Triton client
            self.logger.info(f"Connecting to Triton server at {self.triton_url}")
            self.client = TritonClient(self.triton_url)
            
            # Check if model is ready
            if not await self.client.is_model_ready(self.model_name):
                self.logger.error(f"Model {self.model_name} is not ready on Triton server")
                raise RuntimeError(f"Model {self.model_name} is not ready on Triton server")
            
            self._loaded = True
            self.logger.info(f"Connected to Triton for model {self.model_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Triton: {str(e)}")
            raise
    
    async def unload(self) -> None:
        """
        Unload the client connection.
        """
        if not self.is_loaded():
            return
        
        self.client = None
        self._loaded = False
        self.logger.info("Triton client connection closed")
    
    async def generate(self, 
                      prompt: str, 
                      system_prompt: Optional[str] = None,
                      generation_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text from a prompt using Triton.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt to control model behavior
            generation_config: Configuration for text generation
            
        Returns:
            Generated text
        """
        if not self.is_loaded():
            await self.load()
        
        # Get configuration
        merged_config = self.default_config.copy()
        if generation_config:
            merged_config.update(generation_config)
        
        try:
            # Prepare inputs
            inputs = {
                "prompt": [prompt],
            }
            
            # Add optional inputs
            if system_prompt:
                inputs["system_prompt"] = [system_prompt]
            
            if merged_config:
                inputs["generation_config"] = [json.dumps(merged_config)]
            
            # Run inference
            result = await self.client.infer(
                model_name=self.model_name,
                inputs=inputs,
                outputs=["text_output"]
            )
            
            # Extract generated text
            generated_text = result["text_output"][0].decode('utf-8')
            
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Error during text generation: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "name": self.model_name,
            "type": "llm",
            "backend": "triton",
            "url": self.triton_url,
            "loaded": self.is_loaded(),
            "config": self.default_config
        } 
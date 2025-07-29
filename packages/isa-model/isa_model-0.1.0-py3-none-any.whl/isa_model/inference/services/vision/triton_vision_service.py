import json
import logging
import asyncio
import base64
import io
from PIL import Image
import numpy as np
from typing import Dict, List, Any, AsyncGenerator, Optional, Union

from isa_model.inference.services.base_service import BaseService
from isa_model.inference.providers.triton_provider import TritonProvider

logger = logging.getLogger(__name__)


class TritonVisionService(BaseService):
    """
    Vision service that uses Triton Inference Server to run inference.
    """
    
    def __init__(self, provider: TritonProvider, model_name: str):
        """
        Initialize the Triton Vision service.
        
        Args:
            provider: The Triton provider
            model_name: Name of the model in Triton (e.g., "Gemma3-4B")
        """
        super().__init__(provider, model_name)
        self.client = None
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
    async def _initialize_client(self):
        """Initialize the Triton client"""
        if self.client is None:
            self.client = self.provider.create_client()
            
            # Check if model is ready
            if not self.provider.is_model_ready(self.model_name):
                logger.error(f"Model {self.model_name} is not ready on Triton server")
                raise RuntimeError(f"Model {self.model_name} is not ready on Triton server")
                
            logger.info(f"Initialized Triton client for vision model: {self.model_name}")
    
    async def process_image(self, 
                          image: Union[str, Image.Image, bytes], 
                          prompt: Optional[str] = None,
                          params: Optional[Dict[str, Any]] = None) -> str:
        """
        Process an image and generate a description.
        
        Args:
            image: Input image (PIL Image, base64 string, or bytes)
            prompt: Optional text prompt to guide the model
            params: Generation parameters
            
        Returns:
            Generated text description
        """
        await self._initialize_client()
        
        try:
            import tritonclient.http as httpclient
            
            # Process the image to get numpy array
            image_array = self._prepare_image_input(image)
            
            # Create input tensors for the image
            image_input = httpclient.InferInput("IMAGE", image_array.shape, "UINT8")
            image_input.set_data_from_numpy(image_array)
            inputs = [image_input]
            
            # Add text prompt if provided
            if prompt:
                text_data = np.array([prompt], dtype=np.object_)
                text_input = httpclient.InferInput("TEXT", text_data.shape, "BYTES")
                text_input.set_data_from_numpy(text_data)
                inputs.append(text_input)
            
            # Add parameters if provided
            if params:
                default_params = {
                    "max_new_tokens": 512,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True
                }
                generation_params = {**default_params, **params}
                
                param_json = json.dumps(generation_params)
                param_data = np.array([param_json], dtype=np.object_)
                param_input = httpclient.InferInput("PARAMETERS", param_data.shape, "BYTES")
                param_input.set_data_from_numpy(param_data)
                inputs.append(param_input)
            
            # Create output tensor
            outputs = [httpclient.InferRequestedOutput("TEXT")]
            
            # Send the request
            response = await asyncio.to_thread(
                self.client.infer,
                self.model_name,
                inputs,
                outputs=outputs
            )
            
            # Process the response
            output = response.as_numpy("TEXT")
            response_text = output[0].decode('utf-8')
            
            # Update token usage (estimated since we don't have actual token counts)
            prompt_tokens = len(prompt) // 4 if prompt else 100  # Rough estimate
            completion_tokens = len(response_text) // 4  # Rough estimate
            total_tokens = prompt_tokens + completion_tokens
            
            self.last_token_usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
            
            # Update total token usage
            self.token_usage["prompt_tokens"] += prompt_tokens
            self.token_usage["completion_tokens"] += completion_tokens
            self.token_usage["total_tokens"] += total_tokens
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error during Triton vision inference: {str(e)}")
            raise
    
    def get_token_usage(self) -> Dict[str, int]:
        """
        Get total token usage statistics.
        
        Returns:
            Dictionary with token usage statistics
        """
        return self.token_usage
    
    def get_last_token_usage(self) -> Dict[str, int]:
        """
        Get token usage from last request.
        
        Returns:
            Dictionary with token usage statistics from last request
        """
        return self.last_token_usage
    
    def _prepare_image_input(self, image: Union[str, Image.Image, bytes]) -> np.ndarray:
        """
        Process different types of image inputs into a numpy array.
        
        Args:
            image: Image input (PIL Image, base64 string, or bytes)
            
        Returns:
            Numpy array of the image
        """
        # Convert to PIL image first
        pil_image = self._to_pil_image(image)
        
        # Convert PIL image to numpy array
        return np.array(pil_image)
    
    def _to_pil_image(self, image: Union[str, Image.Image, bytes]) -> Image.Image:
        """
        Convert different image inputs to PIL Image.
        
        Args:
            image: Image input (PIL Image, base64 string, or bytes)
            
        Returns:
            PIL Image
        """
        if isinstance(image, Image.Image):
            return image
        
        elif isinstance(image, str):
            # Check if it's a base64 string
            if image.startswith("data:image"):
                # Extract the base64 part
                image = image.split(",")[1]
            
            try:
                # Try to decode as base64
                image_bytes = base64.b64decode(image)
                return Image.open(io.BytesIO(image_bytes))
            except Exception:
                # Try to open as a file path
                return Image.open(image)
        
        elif isinstance(image, bytes):
            return Image.open(io.BytesIO(image))
        
        else:
            raise ValueError(f"Unsupported image type: {type(image)}") 
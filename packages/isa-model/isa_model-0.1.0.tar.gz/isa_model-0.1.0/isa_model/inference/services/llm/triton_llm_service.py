import json
import logging
import asyncio
from typing import Dict, List, Any, AsyncGenerator, Optional, Union

import numpy as np

from isa_model.inference.services.base_service import BaseLLMService
from isa_model.inference.providers.triton_provider import TritonProvider

logger = logging.getLogger(__name__)


class TritonLLMService(BaseLLMService):
    """
    LLM service that uses Triton Inference Server to run inference.
    """
    
    def __init__(self, provider: TritonProvider, model_name: str):
        """
        Initialize the Triton LLM service.
        
        Args:
            provider: The Triton provider
            model_name: Name of the model in Triton (e.g., "Llama3-8B")
        """
        super().__init__(provider, model_name)
        self.client = None
        self.tokenizer = None
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
                
            logger.info(f"Initialized Triton client for model: {self.model_name}")
    
    async def ainvoke(self, prompt: Union[str, List[Dict[str, str]], Any]) -> str:
        """
        Universal invocation method.
        
        Args:
            prompt: Text prompt or chat messages
        
        Returns:
            Generated text
        """
        if isinstance(prompt, str):
            return await self.acompletion(prompt)
        elif isinstance(prompt, list) and all(isinstance(m, dict) for m in prompt):
            return await self.achat(prompt)
        else:
            raise ValueError("Prompt must be either a string or a list of message dictionaries")
    
    async def achat(self, messages: List[Dict[str, str]]) -> str:
        """
        Chat completion method.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Generated chat response
        """
        # Format chat messages into a single prompt
        formatted_prompt = self._format_chat_messages(messages)
        return await self.acompletion(formatted_prompt)
    
    async def acompletion(self, prompt: str) -> str:
        """
        Text completion method.
        
        Args:
            prompt: Text prompt
            
        Returns:
            Generated text completion
        """
        await self._initialize_client()
        
        try:
            import tritonclient.http as httpclient
            
            # Create input tensors
            input_text = np.array([prompt], dtype=np.object_)
            inputs = [httpclient.InferInput("TEXT", input_text.shape, "BYTES")]
            inputs[0].set_data_from_numpy(input_text)
            
            # Default parameters
            generation_params = {
                "max_new_tokens": self.config.get("max_new_tokens", 512),
                "temperature": self.config.get("temperature", 0.7),
                "top_p": self.config.get("top_p", 0.9),
                "do_sample": self.config.get("temperature", 0.7) > 0
            }
            
            # Add parameters as input tensor
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
            prompt_tokens = len(prompt) // 4  # Rough estimate
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
            logger.error(f"Error during Triton inference: {str(e)}")
            raise
    
    async def agenerate(self, messages: List[Dict[str, str]], n: int = 1) -> List[str]:
        """
        Generate multiple completions.
        
        Args:
            messages: List of message dictionaries
            n: Number of completions to generate
            
        Returns:
            List of generated completions
        """
        results = []
        for _ in range(n):
            result = await self.achat(messages)
            results.append(result)
        return results
    
    async def astream_chat(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Stream chat responses.
        
        Args:
            messages: List of message dictionaries
            
        Yields:
            Generated text chunks
        """
        # For Triton, we don't have true streaming, so we generate the full response
        # and then simulate streaming
        full_response = await self.achat(messages)
        
        # Simulate streaming by yielding words
        words = full_response.split()
        for i in range(len(words)):
            chunk = ' '.join(words[:i+1])
            yield chunk
            await asyncio.sleep(0.05)  # Small delay to simulate streaming
    
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
    
    def _format_chat_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Format chat messages into a single prompt for models that don't support chat natively.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted prompt
        """
        formatted_prompt = ""
        
        for message in messages:
            role = message.get("role", "user").lower()
            content = message.get("content", "")
            
            if role == "system":
                formatted_prompt += f"System: {content}\n\n"
            elif role == "user":
                formatted_prompt += f"User: {content}\n\n"
            elif role == "assistant":
                formatted_prompt += f"Assistant: {content}\n\n"
            else:
                formatted_prompt += f"{role.capitalize()}: {content}\n\n"
        
        formatted_prompt += "Assistant: "
        return formatted_prompt 
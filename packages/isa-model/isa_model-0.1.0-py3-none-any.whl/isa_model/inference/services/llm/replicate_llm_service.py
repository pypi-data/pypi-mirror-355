import logging
from typing import Dict, Any, List, Union, AsyncGenerator, Optional
from isa_model.inference.services.base_service import BaseLLMService
from isa_model.inference.providers.base_provider import BaseProvider
from isa_model.inference.backends.replicate_client import ReplicateBackendClient

logger = logging.getLogger(__name__)

class ReplicateLLMService(BaseLLMService):
    """Replicate LLM service implementation"""
    
    def __init__(self, provider: 'BaseProvider', model_name: str = "meta/llama-3-8b-instruct", backend: Optional[ReplicateBackendClient] = None):
        super().__init__(provider, model_name)
        
        # Use provided backend or create new one
        if backend:
            self.backend = backend
        else:
            api_token = self.config.get("api_token", "")
            self.backend = ReplicateBackendClient(api_token)
            
        # Parse model name for Replicate format (owner/model)
        if "/" not in model_name:
            logger.warning(f"Model name {model_name} is not in Replicate format (owner/model). Using as-is.")
        
        # Store version separately if provided
        self.model_version = None
        if ":" in model_name:
            self.model_name, self.model_version = model_name.split(":", 1)
            
        self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        logger.info(f"Initialized ReplicateLLMService with model {model_name}")
    
    async def ainvoke(self, prompt: Union[str, List[Dict[str, str]], Any]):
        """Universal invocation method"""
        if isinstance(prompt, str):
            return await self.acompletion(prompt)
        elif isinstance(prompt, list):
            return await self.achat(prompt)
        else:
            raise ValueError("Prompt must be string or list of messages")
    
    async def achat(self, messages: List[Dict[str, str]]):
        """Chat completion method"""
        try:
            temperature = self.config.get("temperature", 0.7)
            max_tokens = self.config.get("max_tokens", 1024)
            
            # Convert to Replicate format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Prepare input data
            input_data = {
                "prompt": prompt,
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "system_prompt": self._extract_system_prompt(messages)
            }
            
            # Call Replicate API
            prediction = await self.backend.create_prediction(
                self.model_name, 
                self.model_version, 
                input_data
            )
            
            # Get output - could be a list of strings or a single string
            output = prediction.get("output", "")
            if isinstance(output, list):
                output = "".join(output)
            
            # Approximate token usage - Replicate doesn't provide token counts
            approx_prompt_tokens = len(prompt) // 4  # Very rough approximation
            approx_completion_tokens = len(output) // 4
            self.last_token_usage = {
                "prompt_tokens": approx_prompt_tokens,
                "completion_tokens": approx_completion_tokens,
                "total_tokens": approx_prompt_tokens + approx_completion_tokens
            }
            
            return output
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to Replicate prompt format"""
        prompt = ""
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Skip system prompts - handled separately
            if role == "system":
                continue
                
            if role == "user":
                prompt += f"Human: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
            else:
                # Default to user for unknown roles
                prompt += f"Human: {content}\n\n"
        
        # Add final assistant prefix for the model to continue
        prompt += "Assistant: "
        
        return prompt
    
    def _extract_system_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Extract system prompt from messages"""
        for msg in messages:
            if msg.get("role") == "system":
                return msg.get("content", "")
        return ""
    
    async def acompletion(self, prompt: str):
        """Text completion method"""
        try:
            # For simple completion, use chat format with a single user message
            messages = [{"role": "user", "content": prompt}]
            return await self.achat(messages)
        except Exception as e:
            logger.error(f"Error in text completion: {e}")
            raise
    
    async def agenerate(self, messages: List[Dict[str, str]], n: int = 1) -> List[str]:
        """Generate multiple completions"""
        # Replicate doesn't support multiple outputs in one call,
        # so we make multiple calls
        results = []
        for _ in range(n):
            result = await self.achat(messages)
            results.append(result)
        return results
    
    async def astream_chat(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Stream chat responses"""
        try:
            temperature = self.config.get("temperature", 0.7)
            max_tokens = self.config.get("max_tokens", 1024)
            
            # Convert to Replicate format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Prepare input data
            input_data = {
                "prompt": prompt,
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "system_prompt": self._extract_system_prompt(messages),
                "stream": True
            }
            
            # Call Replicate API with streaming
            async for chunk in self.backend.stream_prediction(
                self.model_name, 
                self.model_version, 
                input_data
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in stream chat: {e}")
            raise
    
    def get_token_usage(self):
        """Get total token usage statistics"""
        return self.last_token_usage
    
    def get_last_token_usage(self) -> Dict[str, int]:
        """Get token usage from last request"""
        return self.last_token_usage
        
    async def close(self):
        """Close the backend client"""
        await self.backend.close() 
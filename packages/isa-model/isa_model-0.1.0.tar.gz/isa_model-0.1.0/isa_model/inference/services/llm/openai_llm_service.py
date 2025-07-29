import logging
from typing import Dict, Any, List, Union, AsyncGenerator, Optional
from isa_model.inference.services.base_service import BaseLLMService
from isa_model.inference.providers.base_provider import BaseProvider
from isa_model.inference.backends.openai_client import OpenAIBackendClient

logger = logging.getLogger(__name__)

class OpenAILLMService(BaseLLMService):
    """OpenAI LLM service implementation"""
    
    def __init__(self, provider: 'BaseProvider', model_name: str = "gpt-3.5-turbo", backend: Optional[OpenAIBackendClient] = None):
        super().__init__(provider, model_name)
        
        # Use provided backend or create new one
        if backend:
            self.backend = backend
        else:
            api_key = self.config.get("api_key", "")
            api_base = self.config.get("api_base", "https://api.openai.com/v1")
            self.backend = OpenAIBackendClient(api_key, api_base)
            
        self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        logger.info(f"Initialized OpenAILLMService with model {model_name}")
    
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
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            response = await self.backend.post("/chat/completions", payload)
            
            # Update token usage
            self.last_token_usage = response.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
            
            return response["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    async def acompletion(self, prompt: str):
        """Text completion method (using chat API since completions is deprecated)"""
        try:
            messages = [{"role": "user", "content": prompt}]
            return await self.achat(messages)
        except Exception as e:
            logger.error(f"Error in text completion: {e}")
            raise
    
    async def agenerate(self, messages: List[Dict[str, str]], n: int = 1) -> List[str]:
        """Generate multiple completions"""
        try:
            temperature = self.config.get("temperature", 0.7)
            max_tokens = self.config.get("max_tokens", 1024)
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "n": n
            }
            response = await self.backend.post("/chat/completions", payload)
            
            # Update token usage
            self.last_token_usage = response.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
            
            return [choice["message"]["content"] for choice in response["choices"]]
        except Exception as e:
            logger.error(f"Error in generate: {e}")
            raise
    
    async def astream_chat(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Stream chat responses"""
        try:
            temperature = self.config.get("temperature", 0.7)
            max_tokens = self.config.get("max_tokens", 1024)
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
            
            async for chunk in self.backend.stream_chat(payload):
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
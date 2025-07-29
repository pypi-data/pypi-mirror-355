import logging
from typing import Dict, Any, List, Union, AsyncGenerator, Optional
from isa_model.inference.services.base_service import BaseLLMService
from isa_model.inference.providers.base_provider import BaseProvider
from isa_model.inference.backends.local_services import OllamaBackendClient

logger = logging.getLogger(__name__)

class OllamaLLMService(BaseLLMService):
    """Ollama LLM service using backend client"""
    
    def __init__(self, provider: 'BaseProvider', model_name: str = "llama3.1", backend: Optional[OllamaBackendClient] = None):
        super().__init__(provider, model_name)
        
        # Use provided backend or create new one
        if backend:
            self.backend = backend
        else:
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 11434)
            self.backend = OllamaBackendClient(host, port)
            
        self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        logger.info(f"Initialized OllamaLLMService with model {model_name}")
    
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
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False
            }
            response = await self.backend.post("/api/chat", payload)
            
            # Update token usage if available
            if "eval_count" in response:
                self.last_token_usage = {
                    "prompt_tokens": response.get("prompt_eval_count", 0),
                    "completion_tokens": response.get("eval_count", 0),
                    "total_tokens": response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
                }
            
            return response["message"]["content"]
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    async def acompletion(self, prompt: str):
        """Text completion method"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            response = await self.backend.post("/api/generate", payload)
            
            # Update token usage if available
            if "eval_count" in response:
                self.last_token_usage = {
                    "prompt_tokens": response.get("prompt_eval_count", 0),
                    "completion_tokens": response.get("eval_count", 0),
                    "total_tokens": response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
                }
            
            return response["response"]
            
        except Exception as e:
            logger.error(f"Error in text completion: {e}")
            raise
    
    async def agenerate(self, messages: List[Dict[str, str]], n: int = 1) -> List[str]:
        """Generate multiple completions"""
        results = []
        for _ in range(n):
            result = await self.achat(messages)
            results.append(result)
        return results
    
    async def astream_chat(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Stream chat responses"""
        # Note: This would require modifying the backend to support streaming
        # For now, return the full response
        response = await self.achat(messages)
        yield response
    
    def get_token_usage(self):
        """Get total token usage statistics"""
        return self.last_token_usage
    
    def get_last_token_usage(self) -> Dict[str, int]:
        """Get token usage from last request"""
        return self.last_token_usage
        
    async def close(self):
        """Close the backend client"""
        await self.backend.close() 
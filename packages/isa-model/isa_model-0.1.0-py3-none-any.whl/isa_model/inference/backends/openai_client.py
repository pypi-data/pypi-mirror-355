import httpx
import logging
from typing import Dict, Any, Optional, AsyncGenerator
import json
import asyncio

logger = logging.getLogger(__name__)

class OpenAIBackendClient:
    """Client for interacting with OpenAI API"""
    
    def __init__(self, api_key: str, api_base: str = "https://api.openai.com/v1", timeout: int = 60):
        """
        Initialize the OpenAI client
        
        Args:
            api_key: OpenAI API key
            api_base: Base URL for OpenAI API
            timeout: Timeout for API calls in seconds
        """
        self.api_key = api_key
        self.api_base = api_base
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        logger.info(f"Initialized OpenAI client with API base: {api_base}")
    
    async def post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a POST request to the OpenAI API
        
        Args:
            endpoint: API endpoint (e.g., /chat/completions)
            payload: Request payload
            
        Returns:
            Response from the API
        """
        url = f"{self.api_base}{endpoint}"
        try:
            response = await self.client.post(url, json=payload, headers=self._headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = {}
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = {"status": e.response.status_code, "text": e.response.text}
                
            logger.error(f"OpenAI API error: {error_detail}")
            raise ValueError(f"OpenAI API error: {error_detail}")
        except Exception as e:
            logger.error(f"Error communicating with OpenAI API: {e}")
            raise
    
    async def stream_chat(self, payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream responses from the chat completion API
        
        Args:
            payload: Request payload (must include 'stream': True)
            
        Yields:
            Response chunks from the API
        """
        url = f"{self.api_base}/chat/completions"
        payload["stream"] = True
        
        try:
            async with self.client.stream("POST", url, json=payload, headers=self._headers) as response:
                response.raise_for_status()
                async for chunk in response.aiter_lines():
                    if not chunk.strip():
                        continue
                    if chunk.startswith("data: "):
                        chunk = chunk[6:]
                    if chunk == "[DONE]":
                        break
                    try:
                        content = json.loads(chunk)
                        if content.get("choices") and len(content["choices"]) > 0:
                            delta = content["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse chunk: {chunk}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing stream chunk: {e}")
                        continue
        except httpx.HTTPStatusError as e:
            error_detail = {}
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = {"status": e.response.status_code, "text": e.response.text}
                
            logger.error(f"OpenAI API streaming error: {error_detail}")
            raise ValueError(f"OpenAI API streaming error: {error_detail}")
        except Exception as e:
            logger.error(f"Error communicating with OpenAI API: {e}")
            raise
    
    async def get_embedding(self, text: str, model: str = "text-embedding-3-small") -> list:
        """
        Get embedding for a text
        
        Args:
            text: Text to embed
            model: Embedding model to use
            
        Returns:
            List of embedding values
        """
        payload = {
            "input": text,
            "model": model
        }
        
        result = await self.post("/embeddings", payload)
        return result["data"][0]["embedding"]
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose() 
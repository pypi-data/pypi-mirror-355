from typing import Dict, Any, List, Optional
from ollama import AsyncClient
from ...base_service import BaseRerankService
from ...base_provider import BaseProvider
from app.config.config_manager import config_manager
import httpx
import asyncio
from functools import wraps

logger = config_manager.get_logger(__name__)

def retry_on_connection_error(max_retries=3, delay=1):
    """Decorator to retry on connection errors"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (httpx.RemoteProtocolError, httpx.ConnectError) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection error on attempt {attempt + 1}, retrying in {delay}s: {str(e)}")
                        await asyncio.sleep(delay)
                    continue
            raise last_error
        return wrapper
    return decorator

class OllamaRerankService(BaseRerankService):
    """Reranking service wrapper around Ollama"""
    
    def __init__(self, provider: 'BaseProvider', model_name: str):
        super().__init__(provider, model_name)
        
        # Initialize the Ollama client for reranking
        self.client = AsyncClient(
            host=self.config.get('base_url', 'http://localhost:11434')
        )
        self.model_name = model_name
    
    @retry_on_connection_error()
    async def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """Rerank documents based on query relevance"""
        try:
            if not query:
                raise ValueError("Query cannot be empty")
            if not documents:
                return []
                
            results = []
            for doc in documents:
                if "content" not in doc:
                    raise ValueError("Each document must have a 'content' field")
                    
                # Format prompt for relevance scoring
                prompt = f"""Rate the relevance of the following text to the query on a scale of 0-100.
Query: {query}
Text: {doc['content']}
Only respond with a number between 0 and 100."""

                # Get relevance score using direct Ollama API
                response = await self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    stream=False
                )
                try:
                    score = float(response.response.strip())
                    score = max(0.0, min(100.0, score)) / 100.0  # Normalize to 0-1
                except ValueError:
                    logger.warning(f"Could not parse score from response: {response.response}")
                    score = 0.0
                    
                # Update document with rerank score
                doc_copy = doc.copy()
                doc_copy["rerank_score"] = score
                doc_copy["final_score"] = doc.get("score", 1.0) * score
                results.append(doc_copy)
            
            # Sort by final score in descending order
            results.sort(key=lambda x: x["final_score"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in rerank: {e}")
            raise
    
    @retry_on_connection_error()
    async def rerank_texts(
        self,
        query: str,
        texts: List[str]
    ) -> List[Dict]:
        """Rerank raw texts based on query relevance"""
        try:
            if not query:
                raise ValueError("Query cannot be empty")
            if not texts:
                return []
                
            # Convert texts to document format
            documents = [{"content": text, "score": 1.0} for text in texts]
            return await self.rerank(query, documents)
            
        except Exception as e:
            logger.error(f"Error in rerank_texts: {str(e)}")
            raise
    
    async def close(self):
        """Cleanup resources"""
        await self.client.aclose()

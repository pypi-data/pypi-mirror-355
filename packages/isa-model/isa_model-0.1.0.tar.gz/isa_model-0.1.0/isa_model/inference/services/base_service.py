from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, AsyncGenerator, TypeVar, Optional
from isa_model.inference.providers.base_provider import BaseProvider

T = TypeVar('T')  # Generic type for responses

class BaseService(ABC):
    """Base class for all AI services"""
    
    def __init__(self, provider: 'BaseProvider', model_name: str):
        self.provider = provider
        self.model_name = model_name
        self.config = provider.get_config()
        
    def __await__(self):
        """Make the service awaitable"""
        yield
        return self

class BaseLLMService(BaseService):
    """Base class for LLM services"""
    
    @abstractmethod
    async def ainvoke(self, prompt: Union[str, List[Dict[str, str]], Any]) -> T:
        """Universal invocation method"""
        pass
    
    @abstractmethod
    async def achat(self, messages: List[Dict[str, str]]) -> T:
        """Chat completion method"""
        pass
    
    @abstractmethod
    async def acompletion(self, prompt: str) -> T:
        """Text completion method"""
        pass
    
    @abstractmethod
    async def agenerate(self, messages: List[Dict[str, str]], n: int = 1) -> List[T]:
        """Generate multiple completions"""
        pass
    
    @abstractmethod
    async def astream_chat(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Stream chat responses"""
        pass
    
    @abstractmethod
    def get_token_usage(self) -> Any:
        """Get total token usage statistics"""
        pass
    
    @abstractmethod
    def get_last_token_usage(self) -> Dict[str, int]:
        """Get token usage from last request"""
        pass

class BaseEmbeddingService(BaseService):
    """Base class for embedding services"""
    
    @abstractmethod
    async def create_text_embedding(self, text: str) -> List[float]:
        """Create embedding for single text"""
        pass
    
    @abstractmethod
    async def create_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts"""
        pass
    
    @abstractmethod
    async def create_chunks(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """Create text chunks with embeddings"""
        pass
    
    @abstractmethod
    async def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute similarity between two embeddings"""
        pass
    
    @abstractmethod
    async def close(self):
        """Cleanup resources"""
        pass

class BaseRerankService(BaseService):
    """Base class for reranking services"""
    
    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """Rerank documents based on query relevance"""
        pass
    
    @abstractmethod
    async def rerank_texts(
        self,
        query: str,
        texts: List[str]
    ) -> List[Dict]:
        """Rerank raw texts based on query relevance"""
        pass

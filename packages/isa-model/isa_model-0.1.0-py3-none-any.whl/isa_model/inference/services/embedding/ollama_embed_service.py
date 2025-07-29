import logging
from typing import List, Dict, Any, Optional
from isa_model.inference.services.base_service import BaseEmbeddingService
from isa_model.inference.providers.base_provider import BaseProvider
from isa_model.inference.backends.local_services import OllamaBackendClient

logger = logging.getLogger(__name__)

class OllamaEmbedService(BaseEmbeddingService):
    """Ollama embedding service using backend client"""
    
    def __init__(self, provider: 'BaseProvider', model_name: str = "bge-m3", backend: Optional[OllamaBackendClient] = None):
        super().__init__(provider, model_name)
        
        # Use provided backend or create new one
        if backend:
            self.backend = backend
        else:
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 11434)
            self.backend = OllamaBackendClient(host, port)
            
        logger.info(f"Initialized OllamaEmbedService with model {model_name}")
    
    async def create_text_embedding(self, text: str) -> List[float]:
        """Create embedding for text"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": text
            }
            response = await self.backend.post("/api/embeddings", payload)
            return response["embedding"]
            
        except Exception as e:
            logger.error(f"Error creating text embedding: {e}")
            raise
    
    async def create_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = await self.create_text_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    async def create_chunks(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """Create text chunks with embeddings"""
        # 简单实现：将文本分成固定大小的块
        chunk_size = 200  # 单词数量
        chunks = []
        
        # 按单词分割
        words = text.split()
        
        # 分块
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i:i+chunk_size])
            embedding = await self.create_text_embedding(chunk_text)
            
            chunk = {
                "text": chunk_text,
                "embedding": embedding,
                "metadata": metadata or {}
            }
            chunks.append(chunk)
            
        return chunks
    
    async def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """计算两个嵌入向量之间的余弦相似度"""
        # 余弦相似度简单实现
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5
        
        if norm1 * norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    async def close(self):
        """Close the backend client"""
        await self.backend.close()


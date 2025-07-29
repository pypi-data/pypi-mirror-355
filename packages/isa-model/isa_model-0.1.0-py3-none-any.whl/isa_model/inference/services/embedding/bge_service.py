import logging
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Union

from isa_model.inference.services.base_service import BaseService
from isa_model.inference.backends.triton_client import TritonClient

logger = logging.getLogger(__name__)


class BgeEmbeddingService(BaseService):
    """
    Service for BGE embedding using Triton Inference Server.
    """
    
    def __init__(self, triton_url: str = "localhost:8001", model_name: str = "bge_embed"):
        """
        Initialize the BGE embedding service.
        
        Args:
            triton_url: URL of the Triton Inference Server
            model_name: Name of the model in Triton
        """
        super().__init__()
        self.triton_url = triton_url
        self.model_name = model_name
        self.client = None
        
        # Default configuration
        self.default_config = {
            "normalize": True
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
    
    async def embed(self, 
                   texts: Union[str, List[str]],
                   normalize: Optional[bool] = None) -> np.ndarray:
        """
        Generate embeddings for texts using Triton.
        
        Args:
            texts: Single text or list of texts to embed
            normalize: Whether to normalize embeddings (if None, use default)
            
        Returns:
            Numpy array of embeddings, shape [batch_size, embedding_dim]
        """
        if not self.is_loaded():
            await self.load()
        
        # Handle single text input
        if isinstance(texts, str):
            texts = [texts]
        
        # Use default normalize setting if not specified
        if normalize is None:
            normalize = self.default_config["normalize"]
        
        try:
            # Prepare inputs
            inputs = {
                "text_input": texts,
                "normalize": np.array([normalize], dtype=bool)
            }
            
            # Run inference
            result = await self.client.infer(
                model_name=self.model_name,
                inputs=inputs,
                outputs=["embedding"]
            )
            
            # Extract embeddings
            embeddings = result["embedding"]
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Error during embedding generation: {str(e)}")
            raise
    
    async def similarity(self, 
                        text1: str, 
                        text2: str,
                        normalize: Optional[bool] = None) -> float:
        """
        Calculate the similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            normalize: Whether to normalize embeddings (if None, use default)
            
        Returns:
            Cosine similarity score (float between -1 and 1)
        """
        # Generate embeddings for both texts
        embeddings = await self.embed([text1, text2], normalize=normalize)
        
        # Calculate cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0]
        
        return float(similarity)
    
    async def batch_similarity(self, 
                              queries: List[str], 
                              documents: List[str],
                              normalize: Optional[bool] = None) -> np.ndarray:
        """
        Calculate similarities between queries and documents.
        
        Args:
            queries: List of query texts
            documents: List of document texts
            normalize: Whether to normalize embeddings (if None, use default)
            
        Returns:
            Numpy array of similarity scores, shape [len(queries), len(documents)]
        """
        # Generate embeddings for queries and documents
        query_embeddings = await self.embed(queries, normalize=normalize)
        doc_embeddings = await self.embed(documents, normalize=normalize)
        
        # Calculate cosine similarities
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_embeddings, doc_embeddings)
        
        return similarities
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "name": self.model_name,
            "type": "embedding",
            "backend": "triton",
            "url": self.triton_url,
            "loaded": self.is_loaded(),
            "embedding_dim": 1024,  # Typical for BGE models
            "config": self.default_config
        } 
import os
import logging
import torch
import numpy as np
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


class BgeEmbedBackend:
    """
    PyTorch backend for the BGE embedding model.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = "auto"):
        """
        Initialize the BGE embedding backend.
        
        Args:
            model_path: Path to the model
            device: Device to run the model on ("cpu", "cuda", or "auto")
        """
        self.model_path = model_path or os.environ.get("BGE_MODEL_PATH", "/models/Bge-m3")
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self._loaded = False
        
        # Default configuration
        self.config = {
            "normalize": True,
            "max_length": 512,
            "pooling_method": "cls"  # Use CLS token for sentence embedding
        }
        
        self.logger = logger
    
    def load(self) -> None:
        """
        Load the model and tokenizer.
        """
        if self._loaded:
            return
        
        try:
            from transformers import AutoModel, AutoTokenizer
            
            # Load tokenizer
            self.logger.info(f"Loading BGE tokenizer from {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Load model
            self.logger.info(f"Loading BGE model on {self.device}")
            if self.device == "cpu":
                self.model = AutoModel.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float32,
                    device_map="auto"
                )
            else:  # cuda
                self.model = AutoModel.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,  # Use half precision on GPU
                    device_map="auto"
                )
            
            self.model.eval()
            self._loaded = True
            self.logger.info("BGE model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load BGE model: {str(e)}")
            raise
    
    def unload(self) -> None:
        """
        Unload the model and tokenizer.
        """
        if not self._loaded:
            return
        
        self.model = None
        self.tokenizer = None
        self._loaded = False
        
        # Force garbage collection
        import gc
        gc.collect()
        
        if self.device == "cuda":
            torch.cuda.empty_cache()
        
        self.logger.info("BGE model unloaded")
    
    def embed(self, 
             texts: Union[str, List[str]],
             normalize: Optional[bool] = None) -> np.ndarray:
        """
        Generate embeddings for texts.
        
        Args:
            texts: Single text or list of texts to embed
            normalize: Whether to normalize embeddings (if None, use default)
            
        Returns:
            Numpy array of embeddings, shape [batch_size, embedding_dim]
        """
        if not self._loaded:
            self.load()
        
        # Handle single text input
        if isinstance(texts, str):
            texts = [texts]
        
        # Use default normalize setting if not specified
        if normalize is None:
            normalize = self.config["normalize"]
        
        try:
            # Tokenize the texts
            inputs = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=self.config["max_length"],
                return_tensors="pt"
            ).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # Use [CLS] token embedding as the sentence embedding
                embeddings = outputs.last_hidden_state[:, 0, :]
                
                # Normalize embeddings if required
                if normalize:
                    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            
            # Convert to numpy array
            embeddings_np = embeddings.cpu().numpy()
            
            return embeddings_np
            
        except Exception as e:
            self.logger.error(f"Error during BGE embedding generation: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "name": "bge-m3",
            "type": "embedding",
            "device": self.device,
            "path": self.model_path,
            "loaded": self._loaded,
            "embedding_dim": 1024,  # Typical for BGE models
            "config": self.config
        }
        
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (float between -1 and 1)
        """
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Reshape if needed
        if embedding1.ndim == 1:
            embedding1 = embedding1.reshape(1, -1)
        if embedding2.ndim == 1:
            embedding2 = embedding2.reshape(1, -1)
            
        # Calculate cosine similarity
        similarity = cosine_similarity(embedding1, embedding2)[0][0]
        
        return float(similarity) 
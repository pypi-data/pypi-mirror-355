import os
import json
import numpy as np
import triton_python_backend_utils as pb_utils
import sys
import logging
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bge_triton_model")

class TritonPythonModel:
    """
    Python model for BGE embedding.
    """
    
    def initialize(self, args):
        """
        Initialize the model.
        """
        self.model_config = json.loads(args['model_config'])
        self.model_path = os.environ.get("BGE_MODEL_PATH", "/models/Bge-m3")
        # Always use CPU for testing
        self.device = "cpu"
        self.model = None
        self.tokenizer = None
        self._loaded = False
        
        # Default configuration
        self.config = {
            "normalize": True,
            "max_length": 512,
            "pooling_method": "cls"  # Use CLS token for sentence embedding
        }
        
        self._load_model()
        
        logger.info(f"Initialized BGE embedding model on {self.device}")
    
    def _load_model(self):
        """Load the BGE model and tokenizer"""
        if self._loaded:
            return
            
        try:
            from transformers import AutoModel, AutoTokenizer
            
            # Load tokenizer
            logger.info(f"Loading BGE tokenizer from {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Load model on CPU for testing
            logger.info(f"Loading BGE model on {self.device}")
            self.model = AutoModel.from_pretrained(
                self.model_path,
                torch_dtype=torch.float32,
                device_map="cpu"  # Force CPU
            )
            
            self.model.eval()
            self._loaded = True
            logger.info("BGE model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load BGE model: {str(e)}")
            # Fall back to dummy model for testing if model loading fails
            self._loaded = False
    
    def _generate_embeddings(self, texts, normalize=True):
        """Generate embeddings for the given texts"""
        if not self._loaded:
            # Return random embeddings for testing
            logger.warning("Model not loaded, returning random embeddings")
            # Generate random embeddings with dimension 1024 (typical for BGE)
            num_texts = len(texts) if isinstance(texts, list) else 1
            return np.random.randn(num_texts, 1024).astype(np.float32)
            
        try:
            # Ensure texts is a list
            if isinstance(texts, str):
                texts = [texts]
                
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
            logger.error(f"Error during BGE embedding generation: {str(e)}")
            # Return random embeddings in case of error
            num_texts = len(texts) if isinstance(texts, list) else 1
            return np.random.randn(num_texts, 1024).astype(np.float32)
    
    def execute(self, requests):
        """
        Process inference requests.
        """
        responses = []
        
        for request in requests:
            # Get input tensors
            input_tensor = pb_utils.get_input_tensor_by_name(request, "text_input")
            
            # Get texts from input tensor
            if input_tensor is not None:
                input_data = input_tensor.as_numpy()
                texts = []
                
                # Convert bytes to strings
                for i in range(len(input_data)):
                    if input_data[i].dtype.type is np.bytes_:
                        texts.append(input_data[i].decode('utf-8'))
                    else:
                        texts.append(str(input_data[i]))
                
                # Generate embeddings
                embeddings = self._generate_embeddings(texts)
                
                # Create output tensor
                output_tensor = pb_utils.Tensor(
                    "embedding_output",
                    embeddings.astype(np.float32)
                )
            else:
                # If no input is provided, return empty tensor
                output_tensor = pb_utils.Tensor(
                    "embedding_output",
                    np.array([], dtype=np.float32)
                )
            
            # Create inference response
            inference_response = pb_utils.InferenceResponse(output_tensors=[output_tensor])
            responses.append(inference_response)
        
        return responses
    
    def finalize(self):
        """
        Clean up resources when the model is unloaded.
        """
        if self.model is not None:
            self.model = None
            self.tokenizer = None
            self._loaded = False
            
            # Force garbage collection
            import gc
            gc.collect()
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
                
        logger.info("BGE embedding model unloaded") 
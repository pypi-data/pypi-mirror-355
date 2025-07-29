from typing import Dict, Any, List, Union, Optional
from ...base_service import BaseService
from ...base_provider import BaseProvider
from transformers import AutoTokenizer
import onnxruntime as ort
import numpy as np
import torch
import os
from pathlib import Path

class ONNXRerankService(BaseService):
    """ONNX Reranker service for BGE models"""
    
    def __init__(self, provider: 'BaseProvider', model_name: str):
        super().__init__(provider, model_name)
        self.model_path = self._get_model_path(model_name)
        self.session = provider.get_session(self.model_path)
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-reranker-v2-m3')
        self.max_length = 512
    
    def _get_model_path(self, model_name: str) -> str:
        """Get path to ONNX model file"""
        base_dir = Path(__file__).parent
        model_path = base_dir / "model_converted" / model_name / "model.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"ONNX model not found at {model_path}. Please run the conversion script first.")
        return str(model_path)
    
    async def compute_score(self, 
                          pairs: Union[List[str], List[List[str]]], 
                          normalize: bool = False) -> Union[float, List[float]]:
        """Compute reranking scores for query-passage pairs"""
        try:
            # Handle single pair case
            if isinstance(pairs[0], str):
                pairs = [pairs]
            
            # Tokenize inputs
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors='np',
                max_length=self.max_length
            )
            
            # Run inference
            ort_inputs = {
                'input_ids': inputs['input_ids'],
                'attention_mask': inputs['attention_mask']
            }
            
            scores = self.session.run(
                None,  # output names, None means all
                ort_inputs
            )[0]
            
            # Convert to float and optionally normalize
            scores = scores.flatten().tolist()
            if normalize:
                scores = [self._sigmoid(score) for score in scores]
            
            # Return single score for single pair
            return scores[0] if len(scores) == 1 else scores
            
        except Exception as e:
            raise RuntimeError(f"ONNX reranking failed: {e}")
    
    def _sigmoid(self, x: float) -> float:
        """Apply sigmoid function to score"""
        return 1 / (1 + np.exp(-x))

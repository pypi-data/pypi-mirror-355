from typing import Dict, Any, List, Union, Optional
from ...base_service import BaseService
from ...base_provider import BaseProvider
from transformers import TableTransformerForObjectDetection, DetrImageProcessor
import torch
from PIL import Image
import numpy as np

class TableTransformerService(BaseService):
    """Table detection service using Microsoft's Table Transformer"""
    
    def __init__(self, provider: 'BaseProvider', model_name: str = "microsoft/table-transformer-detection"):
        super().__init__(provider, model_name)
        self.processor = DetrImageProcessor.from_pretrained(model_name)
        self.model = TableTransformerForObjectDetection.from_pretrained(model_name)
        if torch.cuda.is_available():
            self.model = self.model.cuda()
    
    async def detect_tables(self, image_path: str) -> Dict[str, Any]:
        """Detect tables in image"""
        try:
            # Load and process image
            image = Image.open(image_path)
            inputs = self.processor(images=image, return_tensors="pt")
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Run inference
            outputs = self.model(**inputs)
            
            # Convert outputs to image size
            target_sizes = torch.tensor([image.size[::-1]])
            results = self.processor.post_process_object_detection(
                outputs, target_sizes=target_sizes, threshold=0.7
            )[0]
            
            tables = []
            for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                if label == 1:  # Table class
                    tables.append({
                        "confidence": score.item(),
                        "bbox": box.tolist(),
                        "type": "table"
                    })
            
            return {
                "tables": tables,
                "image_size": image.size
            }
            
        except Exception as e:
            raise RuntimeError(f"Table detection failed: {e}")
    
    async def close(self):
        """Cleanup resources"""
        if hasattr(self, 'model'):
            del self.model
        if hasattr(self, 'processor'):
            del self.processor
        torch.cuda.empty_cache() 
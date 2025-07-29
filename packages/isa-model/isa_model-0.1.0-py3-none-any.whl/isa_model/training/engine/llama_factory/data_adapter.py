"""
Data adapters for LlamaFactory training.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union

from .config import DatasetFormat

logger = logging.getLogger(__name__)


class DataAdapter:
    """
    Base class for adapting datasets to LlamaFactory format.
    
    This class handles converting data from various formats into
    the specific format expected by LlamaFactory.
    
    Example:
        ```python
        # Create a custom adapter
        adapter = CustomAdapter()
        
        # Convert data
        converted_path = adapter.convert_data(
            input_file="path/to/source_data.json",
            output_file="path/to/converted_data.json"
        )
        ```
    """
    
    def __init__(self, format_type: DatasetFormat = DatasetFormat.ALPACA):
        """
        Initialize the data adapter.
        
        Args:
            format_type: The target format to convert to
        """
        self.format_type = format_type
        
    def convert_data(self, input_file: str, output_file: Optional[str] = None) -> str:
        """
        Convert data from input format to LlamaFactory format.
        
        Args:
            input_file: Path to the input data file
            output_file: Path to save the converted data
            
        Returns:
            Path to the converted data file
        """
        if output_file is None:
            dirname = os.path.dirname(input_file)
            basename = os.path.basename(input_file)
            name, ext = os.path.splitext(basename)
            output_file = os.path.join(dirname, f"{name}_converted{ext}")
            
        data = self._load_data(input_file)
        converted_data = self._convert_data(data)
        self._save_data(converted_data, output_file)
        
        return output_file
        
    def _load_data(self, input_file: str) -> Any:
        """
        Load data from the input file.
        
        Args:
            input_file: Path to the input file
            
        Returns:
            Loaded data
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def _save_data(self, data: Any, output_file: str) -> None:
        """
        Save data to the output file.
        
        Args:
            data: Data to save
            output_file: Path to save the data
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def _convert_data(self, data: Any) -> List[Dict[str, Any]]:
        """
        Convert data to the target format.
        
        Args:
            data: Input data
            
        Returns:
            Converted data
        """
        raise NotImplementedError("Subclasses must implement this method")


class AlpacaAdapter(DataAdapter):
    """
    Adapter for Alpaca format data.
    
    Example:
        ```python
        adapter = AlpacaAdapter()
        converted_path = adapter.convert_data("custom_data.json")
        ```
    """
    
    def __init__(self):
        """Initialize the Alpaca adapter."""
        super().__init__(DatasetFormat.ALPACA)
        
    def _convert_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert data to Alpaca format.
        
        Expected output format:
        [
            {
                "instruction": "Task description",
                "input": "Optional input (context)",
                "output": "Expected output"
            },
            ...
        ]
        
        Args:
            data: Input data
            
        Returns:
            Converted data in Alpaca format
        """
        result = []
        
        for item in data:
            if isinstance(item, dict):
                # If already in the expected format, just add to result
                if all(k in item for k in ["instruction", "output"]):
                    alpaca_item = {
                        "instruction": item["instruction"],
                        "input": item.get("input", ""),
                        "output": item["output"]
                    }
                    result.append(alpaca_item)
                # Otherwise, try to convert from common formats
                elif "prompt" in item and "response" in item:
                    alpaca_item = {
                        "instruction": item["prompt"],
                        "input": "",
                        "output": item["response"]
                    }
                    result.append(alpaca_item)
                elif "question" in item and "answer" in item:
                    alpaca_item = {
                        "instruction": item["question"],
                        "input": "",
                        "output": item["answer"]
                    }
                    result.append(alpaca_item)
                else:
                    logger.warning(f"Could not convert item: {item}")
        
        return result


class ShareGPTAdapter(DataAdapter):
    """
    Adapter for ShareGPT format data.
    
    Example:
        ```python
        adapter = ShareGPTAdapter()
        converted_path = adapter.convert_data("sharegpt_data.json")
        ```
    """
    
    def __init__(self):
        """Initialize the ShareGPT adapter."""
        super().__init__(DatasetFormat.SHAREGPT)
        
    def _convert_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert data to ShareGPT format.
        
        Expected output format:
        [
            {
                "conversations": [
                    {"from": "human", "value": "Human message"},
                    {"from": "gpt", "value": "Assistant response"},
                    ...
                ]
            },
            ...
        ]
        
        Args:
            data: Input data
            
        Returns:
            Converted data in ShareGPT format
        """
        result = []
        
        for item in data:
            if isinstance(item, dict):
                conversations = []
                
                # Handle different input formats
                
                # If already in conversations format
                if "conversations" in item and isinstance(item["conversations"], list):
                    # Make sure format is correct
                    for conv in item["conversations"]:
                        if "from" in conv and "value" in conv:
                            # Normalize role names
                            role = conv["from"].lower()
                            if role in ["user", "human"]:
                                role = "human"
                            elif role in ["assistant", "gpt", "ai"]:
                                role = "gpt"
                            else:
                                logger.warning(f"Unknown role: {role}, skipping message")
                                continue
                                
                            conversations.append({
                                "from": role,
                                "value": conv["value"]
                            })
                    
                # If in QA format
                elif "question" in item and "answer" in item:
                    conversations = [
                        {"from": "human", "value": item["question"]},
                        {"from": "gpt", "value": item["answer"]}
                    ]
                
                # If in prompt/response format
                elif "prompt" in item and "response" in item:
                    conversations = [
                        {"from": "human", "value": item["prompt"]},
                        {"from": "gpt", "value": item["response"]}
                    ]
                    
                if conversations:
                    result.append({"conversations": conversations})
        
        return result


class DataAdapterFactory:
    """
    Factory for creating data adapters.
    
    Example:
        ```python
        # Create an adapter based on format
        adapter = DataAdapterFactory.create_adapter(DatasetFormat.ALPACA)
        ```
    """
    
    @staticmethod
    def create_adapter(format_type: DatasetFormat) -> DataAdapter:
        """
        Create a data adapter for the specified format.
        
        Args:
            format_type: The dataset format
            
        Returns:
            A data adapter instance
        """
        if format_type == DatasetFormat.ALPACA:
            return AlpacaAdapter()
        elif format_type == DatasetFormat.SHAREGPT:
            return ShareGPTAdapter()
        else:
            raise ValueError(f"Unsupported format type: {format_type}") 
import os
import logging
import torch
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


class LlamaBackend:
    """
    PyTorch backend for the Llama LLM model.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = "auto"):
        """
        Initialize the Llama backend.
        
        Args:
            model_path: Path to the model
            device: Device to run the model on ("cpu", "cuda", or "auto")
        """
        self.model_path = model_path or os.environ.get("LLAMA_MODEL_PATH", "/models/Llama3-8B")
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self._loaded = False
        
        # Default generation config
        self.default_config = {
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 50,
            "repetition_penalty": 1.1,
            "do_sample": True
        }
        
        self.logger = logger
    
    def load(self) -> None:
        """
        Load the model and tokenizer.
        """
        if self._loaded:
            return
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # Load tokenizer
            self.logger.info(f"Loading Llama tokenizer from {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Load model
            self.logger.info(f"Loading Llama model on {self.device}")
            if self.device == "cpu":
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                    device_map="auto"
                )
            else:  # cuda
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,  # Use half precision on GPU
                    device_map="auto"
                )
            
            self.model.eval()
            self._loaded = True
            self.logger.info("Llama model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load Llama model: {str(e)}")
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
        
        self.logger.info("Llama model unloaded")
    
    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                generation_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt to control model behavior
            generation_config: Configuration for text generation
            
        Returns:
            Generated text
        """
        if not self._loaded:
            self.load()
        
        # Get generation config
        config = self.default_config.copy()
        if generation_config:
            config.update(generation_config)
        
        try:
            # Format the prompt with system prompt if provided
            if system_prompt:
                formatted_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>"
            else:
                formatted_prompt = f"<|user|>\n{prompt}\n<|assistant|>"
            
            # Tokenize the prompt
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)
            
            # Generate text
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    pad_token_id=self.tokenizer.eos_token_id,
                    **config
                )
            
            # Decode the generated text
            generated_text = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            self.logger.error(f"Error during Llama text generation: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "name": "llama3-8b",
            "type": "llm",
            "device": self.device,
            "path": self.model_path,
            "loaded": self._loaded,
            "default_config": self.default_config
        } 
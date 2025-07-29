import os
import json
import numpy as np
import triton_python_backend_utils as pb_utils
import sys
import base64
import torch
from PIL import Image
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gemma_triton_model")

class TritonPythonModel:
    """
    Python model for Gemma Vision LLM (VLM).
    """
    
    def initialize(self, args):
        """
        Initialize the model.
        """
        self.model_config = json.loads(args['model_config'])
        
        # Try different possible model paths
        possible_paths = [
            "/models/Gemma3-4B",  # Original path
            "/models/gemma",      # Alternative path
        ]
        
        # Find the first path that exists
        self.model_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.model_path = path
                logger.info(f"Found model at path: {path}")
                break
                
        if self.model_path is None:
            logger.error("Could not find model path!")
            self.model_path = "/models/Gemma3-4B"  # Default, will fail later
            
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
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
        
        logger.info(f"Initializing Gemma Vision model at {self.model_path} on {self.device}")
        self._load_model()
        
        if self._loaded:
            logger.info("Gemma Vision model initialized successfully")
        else:
            logger.error("Failed to initialize Gemma Vision model")
    
    def _load_model(self):
        """Load the Gemma model and tokenizer"""
        if self._loaded:
            return
            
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # Log environment information
            logger.info(f"Possible model paths:")
            logger.info(f"Current dir: {os.getcwd()}")
            logger.info(f"Model path exists: {os.path.exists(self.model_path)}")
            logger.info(f"Directory listing of /models:")
            if os.path.exists("/models"):
                logger.info(", ".join(os.listdir("/models")))
            
            # Load tokenizer
            logger.info(f"Loading Gemma tokenizer from {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Load model
            logger.info(f"Loading Gemma model on {self.device}")
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
            logger.info("Gemma model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Gemma model: {str(e)}")
            # Fall back to dummy model for testing if model loading fails
            self._loaded = False
    
    def _process_image(self, image_data):
        """Process base64 image data"""
        try:
            # Extract the base64 part if it's a data URL
            if isinstance(image_data, str) and image_data.startswith("data:image"):
                # Extract the base64 part
                image_data = image_data.split(",")[1]
                
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            
            # Open as PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Process for model input if needed
            # For now, we're just returning the image for text description
            return image
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return None
    
    def _generate_text(self, prompt, system_prompt=None, generation_config=None):
        """Generate text using the Gemma model"""
        if not self._loaded:
            return "Model not loaded. Using fallback response: I can see an image but cannot analyze it properly as the vision model is not loaded."
        
        try:
            # Get generation config
            config = self.default_config.copy()
            if generation_config:
                config.update(generation_config)
            
            # Format the prompt with system prompt if provided
            if system_prompt:
                # Gemma uses a specific format for system prompts
                formatted_prompt = f"<bos><start_of_turn>system\n{system_prompt}<end_of_turn>\n<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model"
            else:
                formatted_prompt = f"<bos><start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model"
            
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
            logger.error(f"Error during Gemma text generation: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def execute(self, requests):
        """
        Process inference requests.
        """
        responses = []
        
        for request in requests:
            # Get input tensors
            input_tensor = pb_utils.get_input_tensor_by_name(request, "prompt")
            
            # Convert to string
            if input_tensor is not None:
                input_data = input_tensor.as_numpy()
                if input_data.dtype.type is np.bytes_:
                    input_text = input_data[0][0].decode('utf-8')
                else:
                    input_text = str(input_data[0][0])
                
                # Check if the input contains an image (base64)
                if "data:image" in input_text:
                    # Extract image description query
                    query = "Describe this image in detail."
                    if "?" in input_text:
                        parts = input_text.split("?")
                        query = parts[0] + "?"
                    
                    # For image inputs
                    if self._loaded:
                        response_text = self._generate_text(input_text)
                    else:
                        # Fallback if model not loaded
                        response_text = "Model not loaded. Using fallback response: I can see an image but cannot analyze it properly as the vision model is not loaded."
                else:
                    # For text-only prompts
                    system_prompt_tensor = pb_utils.get_input_tensor_by_name(request, "system_prompt")
                    system_prompt = None
                    if system_prompt_tensor is not None:
                        system_prompt_data = system_prompt_tensor.as_numpy()
                        if system_prompt_data.dtype.type is np.bytes_:
                            system_prompt = system_prompt_data[0].decode('utf-8')
                    
                    response_text = self._generate_text(input_text, system_prompt)
            else:
                response_text = "No input provided"
            
            # Create output tensor
            output_tensor = pb_utils.Tensor(
                "text_output",
                np.array([[response_text]], dtype=np.object_)
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
                
        logger.info("Gemma Vision model unloaded") 
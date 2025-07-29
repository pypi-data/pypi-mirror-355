import os
import logging
import json
import numpy as np
import base64
from typing import Dict, Any, Optional, List, Union

from isa_model.inference.providers.base_provider import BaseProvider
from isa_model.inference.base import ModelType, Capability
from isa_model.inference.providers.model_cache_manager import ModelCacheManager
import asyncio

# 设置日志
logger = logging.getLogger(__name__)

class TritonProvider(BaseProvider):
    """
    Provider for Triton Inference Server models.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Triton provider.
        
        Args:
            config: Configuration for the provider
        """
        super().__init__(config or {})
        
        # Default configuration
        self.default_config = {
            "server_url": os.environ.get("TRITON_SERVER_URL", "localhost:8000"),
            "model_repository": os.environ.get(
                "MODEL_REPOSITORY", 
                os.path.join(os.getcwd(), "models/triton/model_repository")
            ),
            "http_headers": {},
            "verbose": True,
            "client_timeout": 300.0,  # 5 minutes timeout
            "max_batch_size": 8,
            "max_sequence_length": 2048,
            "temperature": 0.7,
            "top_p": 0.9,
            "model_cache_size": 5,  # LRU cache size
            "tokenizer_name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        }
        
        # Merge provided config with defaults
        self.config = {**self.default_config, **self.config}
        
        # Set up logging
        log_level = self.config.get("log_level", "INFO")
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        logger.info(f"Initialized Triton provider with URL: {self.config['server_url']}")
        
        # Initialize model cache manager
        self.model_cache = ModelCacheManager(
            cache_size=self.config.get("model_cache_size"),
            model_repository=self.config.get("model_repository")
        )
        
        # For MLflow Gateway compatibility
        self.triton_url = config.get("triton_url", "localhost:8001")
    
    def get_capabilities(self) -> Dict[ModelType, List[Capability]]:
        """Get provider capabilities by model type"""
        return {
            ModelType.LLM: [
                Capability.CHAT,
                Capability.COMPLETION
            ],
            ModelType.EMBEDDING: [
                Capability.EMBEDDING
            ],
            ModelType.VISION: [
                Capability.IMAGE_UNDERSTANDING
            ]
        }
    
    def get_models(self, model_type: ModelType) -> List[str]:
        """Get available models for given type"""
        # Query the model cache manager for available models
        return self.model_cache.list_available_models(model_type)
    
    async def load_model(self, model_name: str, model_type: ModelType) -> bool:
        """Load a model into Triton server via Model Cache Manager"""
        return await self.model_cache.load_model(model_name, model_type)
    
    async def unload_model(self, model_name: str) -> bool:
        """Unload a model from Triton server"""
        return await self.model_cache.unload_model(model_name)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the configuration for this provider.
        
        Returns:
            Provider configuration
        """
        return self.config
    
    def create_client(self):
        """
        Create a Triton client instance.
        
        Returns:
            Triton HTTP client
        """
        try:
            import tritonclient.http as httpclient
            
            server_url = self.config.get("triton_url", self.config["server_url"])
            
            client = httpclient.InferenceServerClient(
                url=server_url,
                verbose=self.config["verbose"],
                connection_timeout=self.config["client_timeout"],
                network_timeout=self.config["client_timeout"]
            )
            
            return client
        except ImportError:
            logger.error("tritonclient package not installed. Please install with: pip install tritonclient")
            raise
        except Exception as e:
            logger.error(f"Error creating Triton client: {str(e)}")
            raise
    
    def is_server_live(self) -> bool:
        """
        Check if the Triton server is live.
        
        Returns:
            True if the server is live, False otherwise
        """
        try:
            client = self.create_client()
            return client.is_server_live()
        except Exception as e:
            logger.error(f"Error checking server liveness: {str(e)}")
            return False
    
    def is_model_ready(self, model_name: str) -> bool:
        """
        Check if a model is ready on the Triton server.
        
        Args:
            model_name: Name of the model
            
        Returns:
            True if the model is ready, False otherwise
        """
        try:
            client = self.create_client()
            return client.is_model_ready(model_name)
        except Exception as e:
            logger.error(f"Error checking model readiness: {str(e)}")
            return False
    
    def get_model_metadata(self, model_name: str) -> Dict[str, Any]:
        """
        Get metadata for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model metadata
        """
        try:
            client = self.create_client()
            metadata = client.get_model_metadata(model_name)
            return metadata
        except Exception as e:
            logger.error(f"Error getting model metadata: {str(e)}")
            raise
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        Get configuration for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model configuration
        """
        try:
            client = self.create_client()
            config = client.get_model_config(model_name)
            return config
        except Exception as e:
            logger.error(f"Error getting model config: {str(e)}")
            raise
    
    def is_reasoning_model(self, model_name: str) -> bool:
        """Check if the model is optimized for reasoning tasks"""
        # This is a simple implementation, could be enhanced to check model metadata
        return model_name.lower().find("reasoning") != -1 or model_name.lower() in ["llama3", "mistral"]
    
    # Methods for MLflow Gateway compatibility
    
    async def completions(self, prompt: str, model_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate completions for MLflow Gateway.
        
        Args:
            prompt: User prompt text
            model_name: Name of the model to use
            params: Additional parameters
            
        Returns:
            Completion response
        """
        try:
            import tritonclient.http as httpclient
            
            # Create client
            client = self.create_client()
            
            # Generate config
            generation_config = {
                "temperature": params.get("temperature", 0.7),
                "max_new_tokens": params.get("max_tokens", 512),
                "top_p": params.get("top_p", 0.9),
                "top_k": params.get("top_k", 50),
            }
            
            # Prepare inputs
            inputs = []
            
            # Add prompt input
            prompt_data = np.array([prompt], dtype=np.object_)
            prompt_input = httpclient.InferInput("prompt", prompt_data.shape, "BYTES")
            prompt_input.set_data_from_numpy(prompt_data)
            inputs.append(prompt_input)
            
            # Add system prompt if provided
            if "system_prompt" in params:
                system_data = np.array([params["system_prompt"]], dtype=np.object_)
                system_input = httpclient.InferInput("system_prompt", system_data.shape, "BYTES")
                system_input.set_data_from_numpy(system_data)
                inputs.append(system_input)
            
            # Add generation config
            config_data = np.array([json.dumps(generation_config)], dtype=np.object_)
            config_input = httpclient.InferInput("generation_config", config_data.shape, "BYTES")
            config_input.set_data_from_numpy(config_data)
            inputs.append(config_input)
            
            # Create output
            outputs = [httpclient.InferRequestedOutput("text_output")]
            
            # Run inference
            response = await asyncio.to_thread(
                client.infer,
                model_name,
                inputs,
                outputs=outputs
            )
            
            # Process response
            output = response.as_numpy("text_output")
            text = output[0].decode('utf-8')
            
            return {
                "completion": text,
                "metadata": {
                    "model": model_name,
                    "provider": "triton",
                    "token_usage": {
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": len(text.split()),
                        "total_tokens": len(prompt.split()) + len(text.split())
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error during completion: {str(e)}")
            return {
                "error": str(e),
                "metadata": {
                    "model": model_name,
                    "provider": "triton"
                }
            }
    
    async def embeddings(self, text: Union[str, List[str]], model_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate embeddings for MLflow Gateway.
        
        Args:
            text: Text or list of texts to embed
            model_name: Name of the model to use
            params: Additional parameters
            
        Returns:
            Embedding response
        """
        try:
            import tritonclient.http as httpclient
            
            # Create client
            client = self.create_client()
            
            # Normalize parameter
            normalize = params.get("normalize", True)
            
            # Handle input text (convert to list if it's a single string)
            text_list = [text] if isinstance(text, str) else text
            
            # Add text input
            text_data = np.array(text_list, dtype=np.object_)
            text_input = httpclient.InferInput("text_input", text_data.shape, "BYTES")
            text_input.set_data_from_numpy(text_data)
            
            # Add normalize parameter
            normalize_data = np.array([normalize], dtype=bool)
            normalize_input = httpclient.InferInput("normalize", normalize_data.shape, "BOOL")
            normalize_input.set_data_from_numpy(normalize_data)
            
            # Create inputs
            inputs = [text_input, normalize_input]
            
            # Create output
            outputs = [httpclient.InferRequestedOutput("embedding")]
            
            # Run inference
            response = await asyncio.to_thread(
                client.infer,
                model_name,
                inputs,
                outputs=outputs
            )
            
            # Process response
            embedding_output = response.as_numpy("embedding")
            
            return {
                "embedding": embedding_output.tolist(),
                "metadata": {
                    "model": model_name,
                    "provider": "triton",
                    "dimensions": embedding_output.shape[-1]
                }
            }
            
        except Exception as e:
            logger.error(f"Error during embedding: {str(e)}")
            return {
                "error": str(e),
                "metadata": {
                    "model": model_name,
                    "provider": "triton"
                }
            }
    
    async def speech_to_text(self, audio: str, model_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transcribe audio for MLflow Gateway.
        
        Args:
            audio: Base64 encoded audio data or URL
            model_name: Name of the model to use
            params: Additional parameters
            
        Returns:
            Transcription response
        """
        try:
            import tritonclient.http as httpclient
            
            # Create client
            client = self.create_client()
            
            # Decode audio from base64 or download from URL
            if audio.startswith(("http://", "https://")):
                import requests
                audio_data = requests.get(audio).content
            else:
                audio_data = base64.b64decode(audio)
            
            # Language parameter
            language = params.get("language", "en")
            
            # Process audio to get numpy array
            import io
            import librosa
            
            with io.BytesIO(audio_data) as audio_bytes:
                audio_array, _ = librosa.load(audio_bytes, sr=16000)
                audio_array = audio_array.astype(np.float32)
            
            # Create inputs
            audio_input = httpclient.InferInput("audio_input", audio_array.shape, "FP32")
            audio_input.set_data_from_numpy(audio_array)
            
            language_data = np.array([language], dtype=np.object_)
            language_input = httpclient.InferInput("language", language_data.shape, "BYTES")
            language_input.set_data_from_numpy(language_data)
            
            inputs = [audio_input, language_input]
            
            # Create output
            outputs = [httpclient.InferRequestedOutput("text_output")]
            
            # Run inference
            response = await asyncio.to_thread(
                client.infer,
                model_name,
                inputs,
                outputs=outputs
            )
            
            # Process response
            output = response.as_numpy("text_output")
            transcription = output[0].decode('utf-8')
            
            return {
                "text": transcription,
                "metadata": {
                    "model": model_name,
                    "provider": "triton",
                    "language": language
                }
            }
            
        except Exception as e:
            logger.error(f"Error during speech-to-text: {str(e)}")
            return {
                "error": str(e),
                "metadata": {
                    "model": model_name,
                    "provider": "triton"
                }
            } 
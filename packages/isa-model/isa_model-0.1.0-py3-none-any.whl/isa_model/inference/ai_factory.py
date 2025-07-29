from typing import Dict, Type, Any, Optional, Tuple
import logging
from isa_model.inference.providers.base_provider import BaseProvider
from isa_model.inference.services.base_service import BaseService
from isa_model.inference.base import ModelType
import os

from isa_model.inference.services.llm.llama_service import LlamaService
from isa_model.inference.services.llm.gemma_service import GemmaService
from isa_model.inference.services.audio.whisper_service import WhisperService
from isa_model.inference.services.embedding.bge_service import BgeEmbeddingService

# 设置基本的日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIFactory:
    """
    Factory for creating AI services based on the Single Model pattern.
    """
    
    _instance = None
    _is_initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the AI Factory."""
        self.triton_url = os.environ.get("TRITON_URL", "localhost:8001")
        
        # Cache for services (singleton pattern)
        self._llm_services = {}
        self._embedding_services = {}
        self._speech_services = {}
        
        if not self._is_initialized:
            self._providers: Dict[str, Type[BaseProvider]] = {}
            self._services: Dict[Tuple[str, ModelType], Type[BaseService]] = {}
            self._cached_services: Dict[str, BaseService] = {}
            self._initialize_defaults()
            AIFactory._is_initialized = True
    
    def _initialize_defaults(self):
        """Initialize default providers and services"""
        try:
            # Import providers and services
            from isa_model.inference.providers.ollama_provider import OllamaProvider
            from isa_model.inference.services.embedding.ollama_embed_service import OllamaEmbedService
            from isa_model.inference.services.llm.ollama_llm_service import OllamaLLMService
            
            # Register Ollama provider and services
            self.register_provider('ollama', OllamaProvider)
            self.register_service('ollama', ModelType.EMBEDDING, OllamaEmbedService)
            self.register_service('ollama', ModelType.LLM, OllamaLLMService)
            
            # Register OpenAI provider and services
            try:
                from isa_model.inference.providers.openai_provider import OpenAIProvider
                from isa_model.inference.services.llm.openai_llm_service import OpenAILLMService
                
                self.register_provider('openai', OpenAIProvider)
                self.register_service('openai', ModelType.LLM, OpenAILLMService)
                logger.info("OpenAI services registered successfully")
            except ImportError as e:
                logger.warning(f"OpenAI services not available: {e}")
            
            # Register Replicate provider and services
            try:
                from isa_model.inference.providers.replicate_provider import ReplicateProvider
                from isa_model.inference.services.llm.replicate_llm_service import ReplicateLLMService
                from isa_model.inference.services.vision.replicate_vision_service import ReplicateVisionService
                
                self.register_provider('replicate', ReplicateProvider)
                self.register_service('replicate', ModelType.LLM, ReplicateLLMService)
                self.register_service('replicate', ModelType.VISION, ReplicateVisionService)
                logger.info("Replicate services registered successfully")
            except ImportError as e:
                logger.warning(f"Replicate services not available: {e}")
            
            # Try to register Triton services
            try:
                from isa_model.inference.providers.triton_provider import TritonProvider
                from isa_model.inference.services.llm.triton_llm_service import TritonLLMService
                from isa_model.inference.services.vision.triton_vision_service import TritonVisionService
                from isa_model.inference.services.audio.triton_speech_service import TritonSpeechService
                
                self.register_provider('triton', TritonProvider)
                self.register_service('triton', ModelType.LLM, TritonLLMService)
                self.register_service('triton', ModelType.VISION, TritonVisionService)
                self.register_service('triton', ModelType.AUDIO, TritonSpeechService)
                logger.info("Triton services registered successfully")
                
                # Register HuggingFace-based direct LLM service for Llama3-8B
                try:
                    from isa_model.inference.llm.llama3_service import Llama3Service
                    # Register as a standalone service for direct access
                    self._cached_services["llama3"] = Llama3Service()
                    logger.info("Llama3-8B service registered successfully")
                except ImportError as e:
                    logger.warning(f"Llama3-8B service not available: {e}")
                
                # Register HuggingFace-based direct Vision service for Gemma3-4B
                try:
                    from isa_model.inference.vision.gemma3_service import Gemma3VisionService
                    # Register as a standalone service for direct access
                    self._cached_services["gemma3"] = Gemma3VisionService()
                    logger.info("Gemma3-4B Vision service registered successfully")
                except ImportError as e:
                    logger.warning(f"Gemma3-4B Vision service not available: {e}")
                
                # Register HuggingFace-based direct Speech service for Whisper Tiny
                try:
                    from isa_model.inference.speech.whisper_service import WhisperService
                    # Register as a standalone service for direct access
                    self._cached_services["whisper"] = WhisperService()
                    logger.info("Whisper Tiny Speech service registered successfully")
                except ImportError as e:
                    logger.warning(f"Whisper Tiny Speech service not available: {e}")
                
            except ImportError as e:
                logger.warning(f"Triton services not available: {e}")
            
            logger.info("Default AI providers and services initialized with backend architecture")
        except Exception as e:
            logger.error(f"Error initializing default providers and services: {e}")
            # Don't raise - allow factory to work even if some services fail to load
            logger.warning("Some services may not be available due to import errors")
    
    def register_provider(self, name: str, provider_class: Type[BaseProvider]) -> None:
        """Register an AI provider"""
        self._providers[name] = provider_class
    
    def register_service(self, provider_name: str, model_type: ModelType, 
                        service_class: Type[BaseService]) -> None:
        """Register a service type with its provider"""
        self._services[(provider_name, model_type)] = service_class
    
    def create_service(self, provider_name: str, model_type: ModelType, 
                      model_name: str, config: Optional[Dict[str, Any]] = None) -> BaseService:
        """Create a service instance"""
        try:
            cache_key = f"{provider_name}_{model_type}_{model_name}"
            
            if cache_key in self._cached_services:
                return self._cached_services[cache_key]
            
            # 基础配置
            base_config = {
                "log_level": "INFO"
            }
            
            # 合并配置
            service_config = {**base_config, **(config or {})}
            
            # 创建 provider 和 service
            provider_class = self._providers[provider_name]
            service_class = self._services.get((provider_name, model_type))
            
            if not service_class:
                raise ValueError(
                    f"No service registered for provider {provider_name} and model type {model_type}"
                )
            
            provider = provider_class(config=service_config)
            service = service_class(provider=provider, model_name=model_name)
            
            self._cached_services[cache_key] = service
            return service
            
        except Exception as e:
            logger.error(f"Error creating service: {e}")
            raise
    
    # Convenient methods for common services
    def get_llm(self, model_name: str = "llama3.1", provider: str = "ollama",
                config: Optional[Dict[str, Any]] = None) -> BaseService:
        """Get a LLM service instance"""
        
        # Special case for Llama3-8B direct service
        if model_name.lower() in ["llama3", "llama3-8b", "meta-llama-3"]:
            if "llama3" in self._cached_services:
                return self._cached_services["llama3"]
        
        basic_config = {
            "temperature": 0
        }
        if config:
            basic_config.update(config)
        return self.create_service(provider, ModelType.LLM, model_name, basic_config)
    
    def get_vision_model(self, model_name: str = "gemma3-4b", provider: str = "triton",
                       config: Optional[Dict[str, Any]] = None) -> BaseService:
        """Get a vision model service instance"""
        
        # Special case for Gemma3-4B direct service
        if model_name.lower() in ["gemma3", "gemma3-4b", "gemma3-vision"]:
            if "gemma3" in self._cached_services:
                return self._cached_services["gemma3"]
        
        # Special case for Replicate's image generation models
        if provider == "replicate" and "/" in model_name:
            basic_config = {
                "api_token": os.environ.get("REPLICATE_API_TOKEN", ""),
                "guidance_scale": 7.5,
                "num_inference_steps": 30
            }
            if config:
                basic_config.update(config)
            return self.create_service(provider, ModelType.VISION, model_name, basic_config)
        
        basic_config = {
            "temperature": 0.7,
            "max_new_tokens": 512
        }
        if config:
            basic_config.update(config)
        return self.create_service(provider, ModelType.VISION, model_name, basic_config)
    
    def get_embedding(self, model_name: str = "bge-m3", provider: str = "ollama",
                     config: Optional[Dict[str, Any]] = None) -> BaseService:
        """Get an embedding service instance"""
        return self.create_service(provider, ModelType.EMBEDDING, model_name, config)
    
    def get_rerank(self, model_name: str = "bge-m3", provider: str = "ollama",
                   config: Optional[Dict[str, Any]] = None) -> BaseService:
        """Get a rerank service instance"""
        return self.create_service(provider, ModelType.RERANK, model_name, config)
    
    def get_embed_service(self, model_name: str = "bge-m3", provider: str = "ollama",
                         config: Optional[Dict[str, Any]] = None) -> BaseService:
        """Get an embedding service instance"""
        return self.get_embedding(model_name, provider, config)
    
    def get_speech_model(self, model_name: str = "whisper_tiny", provider: str = "triton",
                       config: Optional[Dict[str, Any]] = None) -> BaseService:
        """Get a speech-to-text model service instance"""
        
        # Special case for Whisper Tiny direct service
        if model_name.lower() in ["whisper", "whisper_tiny", "whisper-tiny"]:
            if "whisper" in self._cached_services:
                return self._cached_services["whisper"]
        
        basic_config = {
            "language": "en",
            "task": "transcribe"
        }
        if config:
            basic_config.update(config)
        return self.create_service(provider, ModelType.AUDIO, model_name, basic_config)
    
    async def get_llm_service(self, model_name: str) -> Any:
        """
        Get an LLM service for the specified model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            LLM service instance
        """
        if model_name in self._llm_services:
            return self._llm_services[model_name]
        
        if model_name == "llama":
            service = LlamaService(triton_url=self.triton_url, model_name="llama")
            await service.load()
            self._llm_services[model_name] = service
            return service
        elif model_name == "gemma":
            service = GemmaService(triton_url=self.triton_url, model_name="gemma")
            await service.load()
            self._llm_services[model_name] = service
            return service
        else:
            raise ValueError(f"Unsupported LLM model: {model_name}")
    
    async def get_embedding_service(self, model_name: str) -> Any:
        """
        Get an embedding service for the specified model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Embedding service instance
        """
        if model_name in self._embedding_services:
            return self._embedding_services[model_name]
        
        if model_name == "bge_embed":
            service = BgeEmbeddingService(triton_url=self.triton_url, model_name="bge_embed")
            await service.load()
            self._embedding_services[model_name] = service
            return service
        else:
            raise ValueError(f"Unsupported embedding model: {model_name}")
    
    async def get_speech_service(self, model_name: str) -> Any:
        """
        Get a speech service for the specified model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Speech service instance
        """
        if model_name in self._speech_services:
            return self._speech_services[model_name]
        
        if model_name == "whisper":
            service = WhisperService(triton_url=self.triton_url, model_name="whisper")
            await service.load()
            self._speech_services[model_name] = service
            return service
        else:
            raise ValueError(f"Unsupported speech model: {model_name}")
    
    def get_model_info(self, model_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about available models.
        
        Args:
            model_type: Optional filter for model type
            
        Returns:
            Dict of model information
        """
        models = {
            "llm": [
                {"name": "llama", "description": "Llama3-8B language model"},
                {"name": "gemma", "description": "Gemma3-4B language model"}
            ],
            "embedding": [
                {"name": "bge_embed", "description": "BGE-M3 text embedding model"}
            ],
            "speech": [
                {"name": "whisper", "description": "Whisper-tiny speech-to-text model"}
            ]
        }
        
        if model_type:
            return {model_type: models.get(model_type, [])}
        return models
    
    @classmethod
    def get_instance(cls) -> 'AIFactory':
        """Get the singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
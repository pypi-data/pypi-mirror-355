import logging
import asyncio
import io
import numpy as np
from typing import Dict, Any, Optional, Union, BinaryIO

from isa_model.inference.services.base_service import BaseService
from isa_model.inference.backends.triton_client import TritonClient

logger = logging.getLogger(__name__)


class WhisperService(BaseService):
    """
    Service for Whisper speech-to-text using Triton Inference Server.
    """
    
    def __init__(self, triton_url: str = "localhost:8001", model_name: str = "whisper"):
        """
        Initialize the Whisper service.
        
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
            "language": "en",
            "sampling_rate": 16000
        }
        
        self.logger = logger
    
    async def load(self) -> None:
        """
        Load the client connection to Triton.
        """
        if self.is_loaded():
            return
        
        try:
            from tritonclient.http import InferenceServerClient
            
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
    
    async def transcribe(self, 
                       audio: Union[str, BinaryIO, bytes, np.ndarray], 
                       language: str = "en",
                       config: Optional[Dict[str, Any]] = None) -> str:
        """
        Transcribe audio to text using Triton.
        
        Args:
            audio: Audio input (file path, file-like object, bytes, or numpy array)
            language: Language code (e.g., "en", "fr")
            config: Additional configuration parameters
            
        Returns:
            Transcribed text
        """
        if not self.is_loaded():
            await self.load()
        
        # Process audio to get numpy array
        audio_array = await self._process_audio_input(audio)
        
        # Get configuration
        merged_config = self.default_config.copy()
        if config:
            merged_config.update(config)
        
        # Override language if provided
        if language:
            merged_config["language"] = language
        
        try:
            # Prepare inputs
            inputs = {
                "audio_input": audio_array,
                "language": np.array([merged_config["language"]], dtype=np.object_)
            }
            
            # Run inference
            result = await self.client.infer(
                model_name=self.model_name,
                inputs=inputs,
                outputs=["text_output"]
            )
            
            # Extract transcription
            transcription = result["text_output"][0].decode('utf-8')
            
            return transcription
            
        except Exception as e:
            self.logger.error(f"Error during Whisper transcription: {str(e)}")
            raise
    
    async def _process_audio_input(self, audio: Union[str, BinaryIO, bytes, np.ndarray]) -> np.ndarray:
        """
        Process different types of audio inputs into a numpy array.
        
        Args:
            audio: Audio input (file path, file-like object, bytes, or numpy array)
            
        Returns:
            Numpy array of the audio
        """
        if isinstance(audio, np.ndarray):
            return audio
        
        try:
            import librosa
            
            if isinstance(audio, str):
                # File path
                y, sr = librosa.load(audio, sr=self.default_config["sampling_rate"])
                return y.astype(np.float32)
            
            elif isinstance(audio, (io.IOBase, BinaryIO)):
                # File-like object
                audio.seek(0)
                y, sr = librosa.load(audio, sr=self.default_config["sampling_rate"])
                return y.astype(np.float32)
            
            elif isinstance(audio, bytes):
                # Bytes
                with io.BytesIO(audio) as audio_bytes:
                    y, sr = librosa.load(audio_bytes, sr=self.default_config["sampling_rate"])
                return y.astype(np.float32)
            
            else:
                raise ValueError(f"Unsupported audio type: {type(audio)}")
                
        except ImportError:
            self.logger.error("librosa not installed. Please install with: pip install librosa")
            raise
        except Exception as e:
            self.logger.error(f"Error processing audio: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "name": self.model_name,
            "type": "speech",
            "backend": "triton",
            "url": self.triton_url,
            "loaded": self.is_loaded(),
            "config": self.default_config
        } 
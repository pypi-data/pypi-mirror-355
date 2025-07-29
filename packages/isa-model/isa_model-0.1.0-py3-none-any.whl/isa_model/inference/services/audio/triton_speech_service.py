import json
import logging
import asyncio
import io
import numpy as np
from typing import Dict, List, Any, AsyncGenerator, Optional, Union, BinaryIO

from isa_model.inference.services.base_service import BaseService
from isa_model.inference.providers.triton_provider import TritonProvider

logger = logging.getLogger(__name__)


class TritonSpeechService(BaseService):
    """
    Speech service that uses Triton Inference Server to run speech-to-text inference.
    """
    
    def __init__(self, provider: TritonProvider, model_name: str):
        """
        Initialize the Triton Speech service.
        
        Args:
            provider: The Triton provider
            model_name: Name of the model in Triton (e.g., "whisper_tiny")
        """
        super().__init__(provider, model_name)
        self.client = None
        
    async def _initialize_client(self):
        """Initialize the Triton client"""
        if self.client is None:
            self.client = self.provider.create_client()
            
            # Check if model is ready
            if not self.provider.is_model_ready(self.model_name):
                logger.error(f"Model {self.model_name} is not ready on Triton server")
                raise RuntimeError(f"Model {self.model_name} is not ready on Triton server")
                
            logger.info(f"Initialized Triton client for speech model: {self.model_name}")
    
    async def transcribe(self, 
                       audio: Union[str, BinaryIO, bytes, np.ndarray], 
                       language: str = "en",
                       config: Optional[Dict[str, Any]] = None) -> str:
        """
        Transcribe audio to text using the Triton Inference Server.
        
        Args:
            audio: Audio input (file path, file-like object, bytes, or numpy array)
            language: Language code (e.g., "en", "fr")
            config: Additional configuration parameters
            
        Returns:
            Transcribed text
        """
        await self._initialize_client()
        
        try:
            import tritonclient.http as httpclient
            
            # Process audio to get numpy array
            audio_array = await self._process_audio_input(audio)
            
            # Create input tensors for audio
            audio_input = httpclient.InferInput("audio_input", audio_array.shape, "FP32")
            audio_input.set_data_from_numpy(audio_array)
            inputs = [audio_input]
            
            # Add language input
            language_data = np.array([language], dtype=np.object_)
            language_input = httpclient.InferInput("language", language_data.shape, "BYTES")
            language_input.set_data_from_numpy(language_data)
            inputs.append(language_input)
            
            # Create output tensor
            outputs = [httpclient.InferRequestedOutput("text_output")]
            
            # Send the request
            response = await asyncio.to_thread(
                self.client.infer,
                self.model_name,
                inputs,
                outputs=outputs
            )
            
            # Process the response
            output = response.as_numpy("text_output")
            transcription = output[0].decode('utf-8')
            
            return transcription
            
        except Exception as e:
            logger.error(f"Error during Triton speech inference: {str(e)}")
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
                y, sr = librosa.load(audio, sr=16000)  # Whisper expects 16kHz audio
                return y.astype(np.float32)
            
            elif isinstance(audio, (io.IOBase, BinaryIO)):
                # File-like object
                audio.seek(0)
                y, sr = librosa.load(audio, sr=16000)
                return y.astype(np.float32)
            
            elif isinstance(audio, bytes):
                # Bytes
                with io.BytesIO(audio) as audio_bytes:
                    y, sr = librosa.load(audio_bytes, sr=16000)
                return y.astype(np.float32)
            
            else:
                raise ValueError(f"Unsupported audio type: {type(audio)}")
                
        except ImportError:
            logger.error("librosa not installed. Please install with: pip install librosa")
            raise
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise 
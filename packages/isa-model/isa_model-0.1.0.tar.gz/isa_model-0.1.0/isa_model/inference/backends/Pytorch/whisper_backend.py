import os
import io
import torch
import logging
import numpy as np
from typing import Dict, Any, Optional, Union, BinaryIO

logger = logging.getLogger(__name__)


class WhisperBackend:
    """
    PyTorch backend for the Whisper speech-to-text model.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = "auto"):
        """
        Initialize the Whisper backend.
        
        Args:
            model_path: Path to the model
            device: Device to run the model on ("cpu", "cuda", or "auto")
        """
        self.model_path = model_path or os.environ.get("WHISPER_MODEL_PATH", "/models/Whisper-tiny")
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.processor = None
        self._loaded = False
        
        # Default configuration
        self.config = {
            "language": "en",
            "task": "transcribe",
            "sampling_rate": 16000,
            "chunk_length_s": 30,
            "batch_size": 16
        }
        
        self.logger = logger
    
    def load(self) -> None:
        """
        Load the model and processor.
        """
        if self._loaded:
            return
        
        try:
            from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
            
            # Load processor
            self.logger.info(f"Loading Whisper processor from {self.model_path}")
            self.processor = AutoProcessor.from_pretrained(self.model_path)
            
            # Load model
            self.logger.info(f"Loading Whisper model on {self.device}")
            if self.device == "cpu":
                self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                    device_map="auto"
                )
            else:  # cuda
                self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,  # Use half precision on GPU
                    device_map="auto"
                )
            
            self.model.eval()
            self._loaded = True
            self.logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {str(e)}")
            raise
    
    def unload(self) -> None:
        """
        Unload the model and processor.
        """
        if not self._loaded:
            return
        
        self.model = None
        self.processor = None
        self._loaded = False
        
        # Force garbage collection
        import gc
        gc.collect()
        
        if self.device == "cuda":
            torch.cuda.empty_cache()
        
        self.logger.info("Whisper model unloaded")
    
    def transcribe(self, 
                  audio: Union[np.ndarray, str, BinaryIO, bytes], 
                  language: str = "en",
                  **kwargs) -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio input (numpy array, file path, file-like object, or bytes)
            language: Language code (e.g., "en", "fr")
            kwargs: Additional keyword arguments to override config
            
        Returns:
            Transcribed text
        """
        if not self._loaded:
            self.load()
        
        # Process audio to get numpy array
        audio_array = self._process_audio_input(audio)
        
        # Update config with kwargs
        config = self.config.copy()
        config.update(kwargs)
        config["language"] = language
        
        try:
            # Process audio with processor
            inputs = self.processor(
                audio_array, 
                sampling_rate=config["sampling_rate"],
                return_tensors="pt"
            ).to(self.device)
            
            # Generate transcription
            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    language=config["language"],
                    task=config["task"]
                )
            
            # Decode the output
            transcription = self.processor.batch_decode(
                output, 
                skip_special_tokens=True
            )[0]
            
            return transcription
            
        except Exception as e:
            self.logger.error(f"Error during Whisper transcription: {str(e)}")
            raise
    
    def _process_audio_input(self, audio: Union[np.ndarray, str, BinaryIO, bytes]) -> np.ndarray:
        """
        Process different types of audio inputs into a numpy array.
        
        Args:
            audio: Audio input (numpy array, file path, file-like object, or bytes)
            
        Returns:
            Numpy array of the audio
        """
        if isinstance(audio, np.ndarray):
            return audio
        
        try:
            import librosa
            
            if isinstance(audio, str):
                # File path
                y, sr = librosa.load(audio, sr=self.config["sampling_rate"])
                return y
            
            elif isinstance(audio, (io.IOBase, BinaryIO)):
                # File-like object
                audio.seek(0)
                y, sr = librosa.load(audio, sr=self.config["sampling_rate"])
                return y
            
            elif isinstance(audio, bytes):
                # Bytes
                with io.BytesIO(audio) as audio_bytes:
                    y, sr = librosa.load(audio_bytes, sr=self.config["sampling_rate"])
                return y
            
            else:
                raise ValueError(f"Unsupported audio type: {type(audio)}")
                
        except ImportError:
            self.logger.error("librosa not installed. Please install with: pip install librosa")
            raise
        except Exception as e:
            self.logger.error(f"Error processing audio: {str(e)}")
            raise 
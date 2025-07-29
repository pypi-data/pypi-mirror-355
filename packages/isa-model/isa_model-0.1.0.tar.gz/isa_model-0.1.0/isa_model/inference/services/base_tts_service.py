from abc import abstractmethod
from typing import Dict, Any, Optional, Union, BinaryIO
from .base_service import BaseService

class BaseTTSService(BaseService):
    """Base class for Text-to-Speech services"""
    
    @abstractmethod
    async def generate_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generate speech from text
        
        Args:
            text: The text to convert to speech
            voice_id: Optional voice identifier
            language: Optional language code
            speed: Speech speed factor (1.0 is normal speed)
            options: Additional model-specific options
            
        Returns:
            Audio data as bytes
        """
        pass
    
    @abstractmethod
    async def save_to_file(
        self,
        text: str,
        output_file: Union[str, BinaryIO],
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate speech and save to file
        
        Args:
            text: The text to convert to speech
            output_file: Path to output file or file-like object
            voice_id: Optional voice identifier
            language: Optional language code
            speed: Speech speed factor (1.0 is normal speed)
            options: Additional model-specific options
            
        Returns:
            Path to the saved file
        """
        pass
    
    @abstractmethod
    async def get_available_voices(self) -> Dict[str, Any]:
        """
        Get available voices for the TTS service
        
        Returns:
            Dictionary of available voices with their details
        """
        pass 
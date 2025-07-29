import os
import json
import aiohttp
import asyncio
import base64
import tempfile
from typing import Dict, Any, Optional, Union, BinaryIO, List
from ...base_tts_service import BaseTTSService
from ...providers.runpod_provider import RunPodProvider

class RunPodTTSFishService(BaseTTSService):
    """
    RunPod TTS service using Fish-Speech
    
    This service uses the Fish-Speech TTS model deployed on RunPod to generate speech from text.
    Fish-Speech is a state-of-the-art open-source TTS model that supports multilingual text-to-speech
    and voice cloning capabilities.
    """
    
    def __init__(self, provider: RunPodProvider, model_name: str = "fish-speech"):
        """
        Initialize the RunPod TTS Fish service
        
        Args:
            provider: RunPod provider instance
            model_name: Model name (default: "fish-speech")
        """
        super().__init__(provider, model_name)
        self.api_key = self.config.get("api_key")
        self.endpoint_id = self.config.get("endpoint_id")
        self.base_url = self.config.get("base_url")
        
        if not self.api_key:
            raise ValueError("RunPod API key is required")
        
        if not self.endpoint_id:
            raise ValueError("RunPod endpoint ID is required")
        
        self.endpoint_url = f"{self.base_url}/{self.endpoint_id}/run"
        self.status_url = f"{self.base_url}/{self.endpoint_id}/status"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Default voice reference URLs (can be overridden in the options)
        self.default_voices = {}
    
    async def _run_inference(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run inference on the RunPod endpoint
        
        Args:
            payload: Request payload
            
        Returns:
            Response from the RunPod endpoint
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.endpoint_url,
                headers=self.headers,
                json={"input": payload}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"RunPod API error: {response.status} - {error_text}")
                
                result = await response.json()
                job_id = result.get("id")
                
                if not job_id:
                    raise Exception("No job ID returned from RunPod API")
                
                # Poll for job completion
                while True:
                    async with session.get(
                        f"{self.status_url}/{job_id}",
                        headers=self.headers
                    ) as status_response:
                        status_data = await status_response.json()
                        status = status_data.get("status")
                        
                        if status == "COMPLETED":
                            return status_data.get("output", {})
                        elif status == "FAILED":
                            error = status_data.get("error", "Unknown error")
                            raise Exception(f"RunPod job failed: {error}")
                        
                        # Wait before polling again
                        await asyncio.sleep(1)
    
    async def generate_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generate speech from text using Fish-Speech
        
        Args:
            text: The text to convert to speech
            voice_id: Voice identifier (URL to reference audio)
            language: Language code (auto-detected if not provided)
            speed: Speech speed factor (1.0 is normal speed)
            options: Additional options:
                - gpt_cond_len: GPT conditioning length
                - max_ref_len: Maximum reference length
                - enhance_audio: Whether to enhance audio quality
                
        Returns:
            Audio data as bytes
        """
        options = options or {}
        
        # Prepare the payload
        payload = {
            "text": [[voice_id or "speaker_0", text]],
            "language": language or "auto",
            "speed": speed,
            "gpt_cond_len": options.get("gpt_cond_len", 30),
            "max_ref_len": options.get("max_ref_len", 60),
            "enhance_audio": options.get("enhance_audio", True)
        }
        
        # Add voice reference
        voice_url = None
        if voice_id and voice_id.startswith(("http://", "https://")):
            voice_url = voice_id
        elif voice_id and voice_id in self.default_voices:
            voice_url = self.default_voices[voice_id]
        
        if voice_url:
            payload["voice"] = {"speaker_0": voice_url}
        
        # Run inference
        result = await self._run_inference(payload)
        
        # Extract audio data
        if "audio_base64" in result:
            return base64.b64decode(result["audio_base64"])
        elif "audio_url" in result:
            # Download audio from URL
            async with aiohttp.ClientSession() as session:
                async with session.get(result["audio_url"]) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download audio: {response.status}")
                    return await response.read()
        else:
            raise Exception("No audio data in response")
    
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
            voice_id: Voice identifier
            language: Language code
            speed: Speech speed factor
            options: Additional options
            
        Returns:
            Path to the saved file
        """
        audio_data = await self.generate_speech(text, voice_id, language, speed, options)
        
        if isinstance(output_file, str):
            with open(output_file, "wb") as f:
                f.write(audio_data)
            return output_file
        else:
            output_file.write(audio_data)
            if hasattr(output_file, "name"):
                return output_file.name
            return "audio.wav"
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """
        Get available voices for the TTS service
        
        Returns:
            Dictionary of available voices with their details
        """
        # Fish-Speech doesn't have a fixed set of voices as it uses voice cloning
        # Return the default voices that have been configured
        return {
            "voices": list(self.default_voices.keys()),
            "note": "Fish-Speech supports voice cloning. Provide a URL to a reference audio file to clone a voice."
        }
    
    def add_voice(self, voice_id: str, reference_url: str) -> None:
        """
        Add a voice to the default voices
        
        Args:
            voice_id: Voice identifier
            reference_url: URL to the reference audio file
        """
        self.default_voices[voice_id] = reference_url

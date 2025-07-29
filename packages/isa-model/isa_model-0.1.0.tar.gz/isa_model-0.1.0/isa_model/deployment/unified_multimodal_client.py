#!/usr/bin/env python3
"""
Unified Multimodal Client

This client provides a unified interface to different model types and modalities,
abstracting away the complexity of different backends and deployment strategies.

Features:
- Text generation (chat completion)
- Image generation
- Audio transcription
- Embeddings

Usage:
    from isa_model.deployment.unified_multimodal_client import UnifiedClient
    
    client = UnifiedClient()
    
    # Text generation
    response = client.chat_completion("What is MLflow?")
    
    # Image generation
    image_data = client.generate_image("A beautiful mountain landscape")
    
    # Audio transcription
    transcription = client.transcribe_audio(audio_base64)
    
    # Embeddings
    embeddings = client.get_embeddings("This is a test sentence.")
"""

import os
import json
import base64
import requests
import tempfile
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from PIL import Image
import io

@dataclass
class DeploymentConfig:
    """Deployment configuration for a model type"""
    name: str
    endpoint: str
    api_key: Optional[str] = None

class UnifiedClient:
    """Unified client for multimodal AI models"""
    
    def __init__(self, adapter_url: str = "http://localhost:8300"):
        """Initialize the client with the adapter URL"""
        self.adapter_url = adapter_url
        
        # Configure deployment endpoints - directly to multimodal adapter
        self.deployments = {
            "text": DeploymentConfig(
                name="default",
                endpoint=f"{adapter_url}/v1/chat/completions"
            ),
            "image": DeploymentConfig(
                name="default",
                endpoint=f"{adapter_url}/v1/images/generations"
            ),
            "audio": DeploymentConfig(
                name="default",
                endpoint=f"{adapter_url}/v1/audio/transcriptions"
            ),
            "embeddings": DeploymentConfig(
                name="default",
                endpoint=f"{adapter_url}/v1/embeddings"
            )
        }
    
    def _make_request(self, 
                     deployment_type: str, 
                     payload: Dict[str, Any],
                     files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the specified deployment type"""
        if deployment_type not in self.deployments:
            raise ValueError(f"Unsupported deployment type: {deployment_type}")
            
        deployment = self.deployments[deployment_type]
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if deployment.api_key:
            headers["Authorization"] = f"Bearer {deployment.api_key}"
            
        try:
            if files:
                # For multipart/form-data requests
                response = requests.post(
                    deployment.endpoint,
                    data=payload,
                    files=files
                )
            else:
                # Ensure model is included in the payload
                if "model" not in payload:
                    payload["model"] = deployment.name
                
                # For JSON requests
                response = requests.post(
                    deployment.endpoint,
                    json=payload,
                    headers=headers
                )
                
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error calling {deployment_type} endpoint: {str(e)}")
            print(f"Response: {response.text if 'response' in locals() else 'No response'}")
            raise
    
    def chat_completion(self, 
                       prompt: str, 
                       system_prompt: Optional[str] = None,
                       max_tokens: int = 100,
                       temperature: float = 0.7) -> str:
        """Generate a chat completion response"""
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = self._make_request("text", payload)
        
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        else:
            return "Error: No response generated"
    
    def generate_image(self, 
                      prompt: str, 
                      n: int = 1,
                      size: str = "1024x1024") -> str:
        """Generate an image from a text prompt"""
        payload = {
            "prompt": prompt,
            "n": n,
            "size": size
        }
        
        response = self._make_request("image", payload)
        
        if "data" in response and len(response["data"]) > 0:
            # Return the base64 data URL
            return response["data"][0]["url"]
        else:
            return "Error: No image generated"
    
    def save_image(self, image_data_url: str, output_path: str) -> None:
        """Save a base64 image data URL to a file"""
        if image_data_url.startswith("data:image"):
            # Extract the base64 part from the data URL
            base64_data = image_data_url.split(",")[1]
            
            # Decode the base64 data
            image_data = base64.b64decode(base64_data)
            
            # Save the image
            with open(output_path, "wb") as f:
                f.write(image_data)
                
            print(f"Image saved to {output_path}")
        else:
            raise ValueError("Invalid image data URL format")
    
    def transcribe_audio(self, 
                        audio_data: Union[str, bytes],
                        language: str = "en") -> str:
        """
        Transcribe audio to text
        
        Parameters:
        - audio_data: Either a base64 encoded string or raw bytes
        - language: Language code
        
        Returns:
        - Transcribed text
        """
        # Convert bytes to base64 if needed
        if isinstance(audio_data, bytes):
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        else:
            # Assume it's already base64 encoded
            audio_base64 = audio_data
            
        payload = {
            "file": audio_base64,
            "language": language
        }
        
        response = self._make_request("audio", payload)
        
        if "text" in response:
            return response["text"]
        else:
            return "Error: No transcription generated"
    
    def transcribe_audio_file(self, 
                            file_path: str,
                            language: str = "en") -> str:
        """
        Transcribe an audio file to text
        
        Parameters:
        - file_path: Path to the audio file
        - language: Language code
        
        Returns:
        - Transcribed text
        """
        with open(file_path, "rb") as f:
            audio_data = f.read()
            
        return self.transcribe_audio(audio_data, language)
    
    def get_embeddings(self, 
                      text: Union[str, List[str]]) -> List[List[float]]:
        """
        Get embeddings for text or a list of texts
        
        Parameters:
        - text: Either a single string or a list of strings
        
        Returns:
        - List of embedding vectors
        """
        payload = {
            "input": text
        }
        
        response = self._make_request("embeddings", payload)
        
        if "data" in response:
            return [item["embedding"] for item in response["data"]]
        else:
            return []
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate the cosine similarity between two texts
        
        Parameters:
        - text1: First text
        - text2: Second text
        
        Returns:
        - Cosine similarity (0-1)
        """
        import numpy as np
        
        # Get embeddings for both texts
        embeddings = self.get_embeddings([text1, text2])
        
        if len(embeddings) != 2:
            raise ValueError("Failed to get embeddings for both texts")
            
        # Calculate cosine similarity
        embedding1 = np.array(embeddings[0])
        embedding2 = np.array(embeddings[1])
        
        cos_sim = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        return float(cos_sim)

    def health_check(self) -> bool:
        """Check if the adapter is healthy"""
        try:
            response = requests.get(f"{self.adapter_url}/health")
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {str(e)}")
            return False

if __name__ == "__main__":
    # Test the client
    client = UnifiedClient()
    
    print("\n===== Unified Multimodal Client Demo =====")
    
    # Check health
    if not client.health_check():
        print("Adapter is not healthy. Make sure it's running.")
        exit(1)
    
    # Test chat completion
    print("\nTesting chat completion...")
    response = client.chat_completion(
        "What are the key benefits of MLflow?",
        system_prompt="You are a helpful AI assistant specializing in machine learning.",
        max_tokens=150
    )
    print(f"\nResponse: {response}")
    
    # Test embeddings
    print("\nTesting embeddings...")
    embeddings = client.get_embeddings("What is MLflow?")
    print(f"Embedding dimensionality: {len(embeddings[0])}")
    print(f"First 5 values: {embeddings[0][:5]}")
    
    # Test similarity
    print("\nTesting similarity...")
    similarity = client.similarity(
        "MLflow is a platform for managing machine learning workflows.",
        "MLflow helps data scientists track experiments and deploy models."
    )
    print(f"Similarity: {similarity:.4f}")
    
    # Test image generation
    print("\nTesting image generation...")
    image_url = client.generate_image("A beautiful mountain landscape")
    print(f"Image URL: {image_url[:30]}...")
    
    # Test audio transcription
    print("\nTesting audio transcription...")
    dummy_audio = base64.b64encode(b"dummy audio data").decode("utf-8")
    transcription = client.transcribe_audio(dummy_audio)
    print(f"Transcription: {transcription}")
    
    print("\n===== Demo Complete =====") 
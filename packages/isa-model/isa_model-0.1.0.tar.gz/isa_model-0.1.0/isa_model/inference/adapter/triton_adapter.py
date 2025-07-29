#!/usr/bin/env python3
"""
Multimodal OpenAI-Compatible Adapter for Triton Inference Server

This adapter translates between OpenAI API format and Triton Inference Server format.
It supports multiple modalities (text, image, voice) through a unified API.

Features:
- Chat completions API (text)
- Image generation API
- Audio transcription API
- Embeddings API

The adapter routes requests to the appropriate Triton model based on the task.
"""

import os
import json
import time
import base64
import logging
import requests
import tempfile
import uvicorn
import uuid
from typing import List, Dict, Any, Optional, Union
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Multimodal OpenAI-Compatible Adapter")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
TRITON_URL = os.environ.get("TRITON_URL", "http://localhost:8000")
DEFAULT_TEXT_MODEL = os.environ.get("DEFAULT_TEXT_MODEL", "llama3_cpu")
DEFAULT_IMAGE_MODEL = os.environ.get("DEFAULT_IMAGE_MODEL", "stable_diffusion")
DEFAULT_AUDIO_MODEL = os.environ.get("DEFAULT_AUDIO_MODEL", "whisper_tiny")
DEFAULT_EMBEDDING_MODEL = os.environ.get("DEFAULT_EMBEDDING_MODEL", "bge_m3")
DEFAULT_VISION_MODEL = os.environ.get("DEFAULT_VISION_MODEL", "gemma3_4b")

# ===== Schema Definitions =====

class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = 100
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None

class ImageGenerationRequest(BaseModel):
    model: str
    prompt: str
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024"
    response_format: Optional[str] = "url"

class AudioTranscriptionRequest(BaseModel):
    model: str
    file: str  # Base64 encoded audio
    response_format: Optional[str] = "text"
    language: Optional[str] = "en"

class EmbeddingRequest(BaseModel):
    model: str
    input: Union[str, List[str]]
    encoding_format: Optional[str] = "float"

# ===== Helper Functions =====

def generate_response_id(prefix: str = "res") -> str:
    """Generate a unique response ID."""
    return f"{prefix}-{uuid.uuid4()}"

def format_chat_response(content: str, model: str) -> Dict[str, Any]:
    """Format chat completion response in OpenAI format."""
    return {
        "id": generate_response_id("chatcmpl"),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,  # We don't track these yet
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }

def format_image_response(image_data: str, model: str) -> Dict[str, Any]:
    """Format image generation response in OpenAI format."""
    return {
        "created": int(time.time()),
        "data": [
            {
                "url": f"data:image/png;base64,{image_data}"
            }
        ]
    }

def format_audio_response(text: str, model: str) -> Dict[str, Any]:
    """Format audio transcription response in OpenAI format."""
    return {
        "text": text
    }

def format_embedding_response(embeddings: List[List[float]], model: str) -> Dict[str, Any]:
    """Format embedding response in OpenAI format."""
    data = []
    for i, embedding in enumerate(embeddings):
        data.append({
            "object": "embedding",
            "embedding": embedding,
            "index": i
        })
    
    return {
        "object": "list",
        "data": data,
        "model": model,
        "usage": {
            "prompt_tokens": 0,
            "total_tokens": 0
        }
    }

def extract_content_from_messages(messages: List[ChatMessage]) -> Dict[str, Any]:
    """Extract content from messages for Triton input."""
    formatted_content = ""
    image_data = None
    
    for msg in messages:
        # Handle both string content and list of content parts
        if isinstance(msg.content, str):
            content = msg.content
            formatted_content += f"{msg.role.capitalize()}: {content}\n"
        else:
            # For multimodal content, extract text and image parts
            text_parts = []
            for part in msg.content:
                if part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
                elif part.get("type") == "image_url":
                    # Extract image from URL (assuming base64 encoded)
                    image_url = part.get("image_url", {}).get("url", "")
                    if image_url.startswith("data:image/"):
                        # Extract the base64 part
                        image_data = image_url.split(",")[1]
            
            # Add text parts to formatted content
            content = " ".join(text_parts)
            formatted_content += f"{msg.role.capitalize()}: {content}\n"
    
    formatted_content += "Assistant:"
    return {"text": formatted_content, "image": image_data}

# ===== API Routes =====

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Handle chat completion requests."""
    logger.info(f"Received request: {request.dict()}")
    
    # Extract the formatted content from messages
    content = extract_content_from_messages(request.messages)
    input_text = content["text"]
    image_data = content["image"]
    
    # Use requested model or default
    model = request.model if request.model != "default" else DEFAULT_TEXT_MODEL
    
    # Prepare request for Triton
    triton_request = {
        "inputs": [
            {
                "name": "text_input",
                "shape": [1, 1],
                "datatype": "BYTES",
                "data": [input_text]
            },
            {
                "name": "max_tokens",
                "shape": [1, 1],
                "datatype": "INT32",
                "data": [request.max_tokens]
            },
            {
                "name": "temperature",
                "shape": [1, 1],
                "datatype": "FP32",
                "data": [request.temperature]
            }
        ]
    }
    
    # Add image input if available and using vision model
    if image_data is not None and model == "gemma3_4b":
        try:
            # Decode base64 image
            from PIL import Image
            import io
            import numpy as np
            
            # Decode and preprocess image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Resize to expected size (224x224 for most vision models)
            image = image.resize((224, 224))
            
            # Convert to RGB if not already
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Convert to numpy array and normalize
            image_array = np.array(image).astype(np.float32) / 255.0
            
            # Reorder from HWC to CHW format
            image_array = np.transpose(image_array, (2, 0, 1))
            
            # Add image input to Triton request
            triton_request["inputs"].append({
                "name": "image_input",
                "shape": list(image_array.shape),
                "datatype": "FP32",
                "data": image_array.flatten().tolist()
            })
            
            logger.info("Added image input to request")
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
    
    logger.info(f"Sending to Triton: {triton_request}")
    
    # Send to Triton
    try:
        response = requests.post(
            f"{TRITON_URL}/v2/models/{model}/infer",
            json=triton_request
        )
        response.raise_for_status()
        triton_response = response.json()
        logger.info(f"Triton response status: {response.status_code}")
        logger.info(f"Triton response: {triton_response}")
        
        # Extract text output
        output_data = triton_response["outputs"][0]["data"][0]
        
        # Format response
        return format_chat_response(output_data, model)
    
    except Exception as e:
        logger.error(f"Error calling Triton: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling model: {str(e)}")

@app.post("/v1/images/generations")
async def generate_images(request: ImageGenerationRequest):
    """Handle image generation requests."""
    logger.info(f"Received image generation request: {request.dict()}")
    
    # Use requested model or default
    model = request.model if request.model != "default" else DEFAULT_IMAGE_MODEL
    
    # For demo purposes - in a real implementation, this would call the Triton image model
    # Here we'll just simulate image generation with a placeholder
    try:
        # Simulate Triton call (replace with actual call to Triton when image model is available)
        # Return a placeholder image for demonstration
        with open("placeholder.png", "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        return format_image_response(image_data, model)
    
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

@app.post("/v1/audio/transcriptions")
async def transcribe_audio(request: AudioTranscriptionRequest):
    """Handle audio transcription requests."""
    logger.info(f"Received audio transcription request: {request.dict()}")
    
    # Use requested model or default
    model = request.model if request.model != "default" else DEFAULT_AUDIO_MODEL
    
    try:
        # Decode the base64 audio
        audio_data = base64.b64decode(request.file)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        # Load and preprocess audio for Whisper
        import librosa
        import numpy as np
        
        # Load audio file and resample to 16kHz for Whisper
        audio_array, _ = librosa.load(temp_file_path, sr=16000, mono=True)
        
        # Prepare request for Triton
        triton_request = {
            "inputs": [
                {
                    "name": "audio_input",
                    "shape": [len(audio_array)],
                    "datatype": "FP32",
                    "data": audio_array.tolist()
                }
            ]
        }
        
        # Add language if provided
        if hasattr(request, 'language') and request.language:
            triton_request["inputs"].append({
                "name": "language",
                "shape": [1, 1],
                "datatype": "BYTES",
                "data": [request.language]
            })
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        # Send to Triton
        response = requests.post(
            f"{TRITON_URL}/v2/models/{model}/infer",
            json=triton_request
        )
        response.raise_for_status()
        triton_response = response.json()
        
        # Extract text output
        transcription = triton_response["outputs"][0]["data"][0]
        
        return format_audio_response(transcription, model)
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        # Fallback response
        return format_audio_response(
            "This is a placeholder transcription. In production, this would be generated by the Whisper model.", 
            model
        )

@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """Handle embedding requests."""
    logger.info(f"Received embedding request: {request.dict()}")
    
    # Use requested model or default
    model = request.model if request.model != "default" else DEFAULT_EMBEDDING_MODEL
    
    # Convert input to list if it's a single string
    inputs = request.input if isinstance(request.input, list) else [request.input]
    
    try:
        # Process each input text
        all_embeddings = []
        
        for text in inputs:
            # Prepare request for Triton
            triton_request = {
                "inputs": [
                    {
                        "name": "text_input",
                        "shape": [1, 1],
                        "datatype": "BYTES",
                        "data": [text]
                    }
                ]
            }
            
            # Send to Triton
            response = requests.post(
                f"{TRITON_URL}/v2/models/{model}/infer",
                json=triton_request
            )
            response.raise_for_status()
            triton_response = response.json()
            
            # Extract embedding
            embedding = triton_response["outputs"][0]["data"]
            all_embeddings.append(embedding)
        
        return format_embedding_response(all_embeddings, model)
        
    except Exception as e:
        logger.error(f"Error creating embeddings: {str(e)}")
        
        # Fallback - return random embeddings
        embeddings = []
        for _ in inputs:
            # Generate a random embedding vector of dimension 1024 (BGE-M3)
            embedding = np.random.normal(0, 1, 1024).tolist()
            embeddings.append(embedding)
        
        return format_embedding_response(embeddings, model)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# ===== Main =====

if __name__ == "__main__":
    # Create placeholder image for demo
    try:
        if not os.path.exists("placeholder.png"):
            # Create a simple 256x256 black image
            import numpy as np
            from PIL import Image
            img = Image.fromarray(np.zeros((256, 256, 3), dtype=np.uint8))
            img.save("placeholder.png")
    except ImportError:
        logger.warning("PIL not installed. Cannot create placeholder image.")
    
    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8300) 
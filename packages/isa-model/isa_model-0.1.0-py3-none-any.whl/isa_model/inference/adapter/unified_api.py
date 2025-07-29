import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from isa_model.inference.ai_factory import AIFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("unified_api")

# Create FastAPI app
app = FastAPI(
    title="Unified AI Model API",
    description="API for inference with Llama3-8B, Gemma3-4B, Whisper, and BGE-M3 models",
    version="1.0.0"
)

# Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (system, user, assistant)")
    content: str = Field(..., description="Content of the message")

class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model ID to use (llama, gemma)")
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    max_tokens: Optional[int] = Field(512, description="Maximum number of tokens to generate")
    top_p: Optional[float] = Field(0.9, description="Top-p sampling parameter")
    top_k: Optional[int] = Field(50, description="Top-k sampling parameter")

class ChatCompletionResponse(BaseModel):
    model: str = Field(..., description="Model used for completion")
    choices: List[Dict[str, Any]] = Field(..., description="Generated completions")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")

class EmbeddingRequest(BaseModel):
    model: str = Field(..., description="Model ID to use (bge_embed)")
    input: Union[str, List[str]] = Field(..., description="Text to embed")
    normalize: Optional[bool] = Field(True, description="Whether to normalize embeddings")

class TranscriptionRequest(BaseModel):
    model: str = Field(..., description="Model ID to use (whisper)")
    audio: str = Field(..., description="Base64-encoded audio data or URL")
    language: Optional[str] = Field("en", description="Language code")

# Factory for creating services
ai_factory = AIFactory()

# Dependency to get LLM service
async def get_llm_service(model: str):
    if model == "llama":
        return await ai_factory.get_llm_service("llama")
    elif model == "gemma":
        return await ai_factory.get_llm_service("gemma")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

# Dependency to get embedding service
async def get_embedding_service(model: str):
    if model == "bge_embed":
        return await ai_factory.get_embedding_service("bge_embed")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

# Dependency to get speech service
async def get_speech_service(model: str):
    if model == "whisper":
        return await ai_factory.get_speech_service("whisper")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

# Endpoints
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(request: ChatCompletionRequest):
    """Generate chat completion"""
    try:
        # Get the appropriate service
        service = await get_llm_service(request.model)
        
        # Format messages
        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Extract system prompt if present
        system_prompt = None
        if formatted_messages and formatted_messages[0]["role"] == "system":
            system_prompt = formatted_messages[0]["content"]
            formatted_messages = formatted_messages[1:]
        
        # Get user prompt (last user message)
        user_prompt = ""
        for msg in reversed(formatted_messages):
            if msg["role"] == "user":
                user_prompt = msg["content"]
                break
        
        if not user_prompt:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Set generation config
        generation_config = {
            "temperature": request.temperature,
            "max_new_tokens": request.max_tokens,
            "top_p": request.top_p,
            "top_k": request.top_k
        }
        
        # Generate completion
        completion = await service.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            generation_config=generation_config
        )
        
        # Format response
        response = {
            "model": request.model,
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": completion
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ],
            "usage": {
                "prompt_tokens": len(user_prompt.split()),
                "completion_tokens": len(completion.split()),
                "total_tokens": len(user_prompt.split()) + len(completion.split())
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/embeddings")
async def create_embedding(request: EmbeddingRequest):
    """Generate embeddings for text"""
    try:
        # Get the embedding service
        service = await get_embedding_service("bge_embed")
        
        # Generate embeddings
        if isinstance(request.input, str):
            embeddings = await service.embed(request.input, normalize=request.normalize)
            data = [{"embedding": embeddings[0].tolist(), "index": 0}]
        else:
            embeddings = await service.embed(request.input, normalize=request.normalize)
            data = [{"embedding": emb.tolist(), "index": i} for i, emb in enumerate(embeddings)]
        
        # Format response
        response = {
            "model": request.model,
            "data": data,
            "usage": {
                "prompt_tokens": sum(len(text.split()) for text in (request.input if isinstance(request.input, list) else [request.input])),
                "total_tokens": sum(len(text.split()) for text in (request.input if isinstance(request.input, list) else [request.input]))
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in embedding generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/audio/transcriptions")
async def transcribe_audio(request: TranscriptionRequest):
    """Transcribe audio to text"""
    try:
        import base64
        
        # Get the speech service
        service = await get_speech_service("whisper")
        
        # Process audio
        if request.audio.startswith(("http://", "https://")):
            # URL - download audio
            import requests
            audio_data = requests.get(request.audio).content
        else:
            # Base64 - decode
            audio_data = base64.b64decode(request.audio)
        
        # Transcribe
        transcription = await service.transcribe(
            audio=audio_data, 
            language=request.language
        )
        
        # Format response
        response = {
            "model": request.model,
            "text": transcription
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in audio transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Model info endpoint
@app.get("/v1/models")
async def list_models():
    """List available models"""
    models = [
        {
            "id": "llama",
            "type": "llm",
            "description": "Llama3-8B language model"
        },
        {
            "id": "gemma",
            "type": "llm",
            "description": "Gemma3-4B language model"
        },
        {
            "id": "whisper",
            "type": "speech",
            "description": "Whisper-tiny speech-to-text model"
        },
        {
            "id": "bge_embed",
            "type": "embedding",
            "description": "BGE-M3 text embedding model"
        }
    ]
    
    return {"data": models}

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 
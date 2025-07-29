import os
import base64
import tempfile
import runpod
import torch
import torchaudio
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Union

# Add Fish-Speech to the Python path
sys.path.append('/app/fish-speech')

# Import Fish-Speech modules
from fish_speech.models.fish_speech.model import FishSpeech
from fish_speech.models.fish_speech.config import FishSpeechConfig
from fish_speech.utils.audio import load_audio, save_audio
from fish_speech.utils.tokenizer import load_tokenizer

# Load the model
MODEL_PATH = "/app/models/fish_speech_v1.4.0.pth"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Initialize the model
def load_model():
    print("Loading Fish-Speech model...")
    config = FishSpeechConfig()
    model = FishSpeech(config)
    
    # Load the model weights
    checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    model.to(DEVICE)
    
    # Load the tokenizer
    tokenizer = load_tokenizer()
    
    print(f"Model loaded successfully on {DEVICE}")
    return model, tokenizer

model, tokenizer = load_model()

# Download a file from a URL
async def download_file(url: str) -> str:
    import aiohttp
    import os
    
    # Create a temporary file
    temp_dir = tempfile.mkdtemp()
    local_filename = os.path.join(temp_dir, "reference_audio.wav")
    
    # Download the file
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to download file: {response.status}")
            
            with open(local_filename, "wb") as f:
                f.write(await response.read())
    
    return local_filename

# Generate speech using Fish-Speech
def generate_speech(
    text: str,
    reference_audio_path: str = None,
    language: str = "auto",
    speed: float = 1.0,
    gpt_cond_len: int = 30,
    max_ref_len: int = 60,
    enhance_audio: bool = True
) -> str:
    """
    Generate speech using Fish-Speech
    
    Args:
        text: Text to convert to speech
        reference_audio_path: Path to reference audio file for voice cloning
        language: Language code (auto for auto-detection)
        speed: Speech speed factor
        gpt_cond_len: GPT conditioning length
        max_ref_len: Maximum reference length
        enhance_audio: Whether to enhance audio quality
        
    Returns:
        Path to the generated audio file
    """
    print(f"Generating speech for text: {text}")
    
    # Load reference audio if provided
    reference = None
    if reference_audio_path:
        print(f"Loading reference audio: {reference_audio_path}")
        reference, sr = load_audio(reference_audio_path)
        reference = reference.to(DEVICE)
    
    # Generate speech
    with torch.no_grad():
        # Tokenize the text
        tokens = tokenizer.encode(text, language=language)
        tokens = torch.tensor(tokens, dtype=torch.long, device=DEVICE).unsqueeze(0)
        
        # Generate speech
        output = model.generate(
            tokens,
            reference=reference,
            gpt_cond_latent_length=gpt_cond_len,
            max_ref_length=max_ref_len,
            top_k=50,
            top_p=0.95,
            temperature=0.7,
            speed=speed
        )
        
        # Get the audio
        audio = output["audio"]
        
        # Enhance audio if requested
        if enhance_audio:
            # Apply simple normalization
            audio = audio / torch.max(torch.abs(audio))
        
        # Save the audio to a temporary file
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "output.wav")
        save_audio(audio.cpu(), output_path, sample_rate=24000)
        
        print(f"Speech generated successfully: {output_path}")
        return output_path

# RunPod handler
def handler(event):
    """
    RunPod handler function
    
    Args:
        event: RunPod event object
        
    Returns:
        Dictionary with the generated audio
    """
    try:
        # Get the input data
        input_data = event.get("input", {})
        
        # Extract parameters
        text_data = input_data.get("text", [])
        language = input_data.get("language", "auto")
        speed = input_data.get("speed", 1.0)
        gpt_cond_len = input_data.get("gpt_cond_len", 30)
        max_ref_len = input_data.get("max_ref_len", 60)
        enhance_audio = input_data.get("enhance_audio", True)
        voice_data = input_data.get("voice", {})
        
        # Validate input
        if not text_data:
            return {"error": "No text provided"}
        
        # Process each text segment
        results = []
        
        # Download reference audio if provided
        reference_audio_paths = {}
        for speaker_id, url in voice_data.items():
            if url:
                # Use runpod.download_file for synchronous download
                local_path = runpod.download_file(url)
                reference_audio_paths[speaker_id] = local_path
        
        # Process each text segment
        for speaker_id, text in text_data:
            # Get reference audio path
            reference_path = reference_audio_paths.get(speaker_id)
            
            # Generate speech
            output_path = generate_speech(
                text=text,
                reference_audio_path=reference_path,
                language=language,
                speed=speed,
                gpt_cond_len=gpt_cond_len,
                max_ref_len=max_ref_len,
                enhance_audio=enhance_audio
            )
            
            # Read the audio file and convert to base64
            with open(output_path, "rb") as f:
                audio_data = f.read()
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            
            # Add to results
            results.append({
                "speaker_id": speaker_id,
                "text": text,
                "audio_base64": audio_base64
            })
        
        # Return the results
        return {
            "audio_base64": results[0]["audio_base64"] if results else None,
            "results": results
        }
    
    except Exception as e:
        import traceback
        error_message = str(e)
        stack_trace = traceback.format_exc()
        print(f"Error: {error_message}")
        print(f"Stack trace: {stack_trace}")
        return {"error": error_message, "stack_trace": stack_trace}

# Start the RunPod handler
runpod.serverless.start({"handler": handler}) 
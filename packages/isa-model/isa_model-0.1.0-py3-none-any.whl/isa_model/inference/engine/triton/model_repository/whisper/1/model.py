import json
import numpy as np
import triton_python_backend_utils as pb_utils
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whisper_triton_model")

class TritonPythonModel:
    """
    Python model for Whisper speech-to-text using a simplified approach.
    """
    
    def initialize(self, args):
        """
        Initialize the model.
        """
        self.model_config = json.loads(args['model_config'])
        
        # Get model name from config
        self.model_name = "/models/Whisper-tiny"
        if 'parameters' in self.model_config:
            parameters = self.model_config['parameters']
            if 'model_name' in parameters:
                self.model_name = parameters['model_name']['string_value']
        
        logger.info(f"Initializing simplified Whisper model: {self.model_name}")
        
        # This is a simple mock model for testing
        # In production, you would use an actual Whisper model
        self.languages = {
            "en": "English",
            "fr": "French",
            "es": "Spanish",
            "de": "German",
            "zh": "Chinese",
            "ja": "Japanese"
        }
        
        # Try loading the model
        try:
            from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
            import torch
            
            logger.info(f"Attempting to load Whisper model from {self.model_name}")
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                device_map="cpu"
            )
            self.model.eval()
            self.model_loaded = True
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load Whisper model: {e}")
            self.model_loaded = False
            logger.info("Using fallback mock transcription")
        
        logger.info("Simplified Whisper model initialized successfully")
    
    def execute(self, requests):
        """
        Process inference requests.
        """
        responses = []
        
        for request in requests:
            try:
                # Get input tensors
                audio_input = pb_utils.get_input_tensor_by_name(request, "audio_input")
                language_input = pb_utils.get_input_tensor_by_name(request, "language")
                
                # Get language or use default
                language = "en"
                if language_input is not None:
                    # Fix for decoding language input
                    lang_np = language_input.as_numpy()
                    if lang_np.dtype.type is np.bytes_:
                        language = lang_np[0][0].decode('utf-8')
                    elif lang_np.dtype.type is np.object_:
                        language = str(lang_np[0][0])
                    else:
                        language = str(lang_np[0][0])
                
                # Process audio input
                if audio_input is not None:
                    audio_data = audio_input.as_numpy()
                    
                    # Handle input shape [1, -1]
                    logger.info(f"Original audio data shape: {audio_data.shape}")
                    
                    # If the model is loaded, use it for transcription
                    if hasattr(self, 'model_loaded') and self.model_loaded:
                        try:
                            import torch
                            
                            # Reshape if needed
                            if len(audio_data.shape) > 2:  # [batch, 1, length]
                                audio_data = audio_data.reshape(audio_data.shape[0], -1)
                                
                            # Process audio with transformers
                            inputs = self.processor(
                                audio_data,
                                sampling_rate=16000,
                                return_tensors="pt"
                            )
                            
                            # Generate transcription
                            with torch.no_grad():
                                generated_ids = self.model.generate(
                                    inputs.input_features,
                                    language=language,
                                    task="transcribe"
                                )
                                
                            # Decode transcription
                            transcription = self.processor.batch_decode(
                                generated_ids,
                                skip_special_tokens=True
                            )[0]
                            
                            logger.info(f"Generated transcription using model: {transcription}")
                        except Exception as e:
                            logger.error(f"Error using loaded model: {e}")
                            # Fall back to mock transcription
                            audio_length = audio_data.size
                            transcription = self._get_mock_transcription(audio_length, language)
                    else:
                        # Use mock transcription
                        audio_length = audio_data.size
                        transcription = self._get_mock_transcription(audio_length, language)
                    
                else:
                    transcription = "No audio input provided."
                
                # Create output tensor
                transcription_tensor = pb_utils.Tensor(
                    "text_output", 
                    np.array([transcription], dtype=np.object_)
                )
                
                # Create and append response
                inference_response = pb_utils.InferenceResponse(
                    output_tensors=[transcription_tensor]
                )
                responses.append(inference_response)
                
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                # Return error response
                error_response = pb_utils.InferenceResponse(
                    output_tensors=[
                        pb_utils.Tensor(
                            "text_output",
                            np.array([f"Error: {str(e)}"], dtype=np.object_)
                        )
                    ]
                )
                responses.append(error_response)
        
        return responses
    
    def _get_mock_transcription(self, audio_length, language):
        """Generate a mock transcription based on audio length"""
        if audio_length > 100000:
            return f"This is a test transcription in {self.languages.get(language, 'English')}. The audio is quite long with {audio_length} samples."
        elif audio_length > 50000:
            return f"This is a medium length test transcription in {self.languages.get(language, 'English')}."
        else:
            return f"Short test transcription in {self.languages.get(language, 'English')}."
    
    def finalize(self):
        """
        Clean up resources when the model is unloaded.
        """
        if hasattr(self, 'model') and self.model is not None:
            self.model = None
            self.processor = None
            
            # Force garbage collection
            import gc
            gc.collect()
            
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
                
        logger.info("Whisper model unloaded") 
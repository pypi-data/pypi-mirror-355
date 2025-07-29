import json
import numpy as np
import triton_python_backend_utils as pb_utils
import random

class TritonPythonModel:
    """
    Simulated Llama model for testing.
    """
    
    def initialize(self, args):
        """
        Initialize the model.
        """
        self.model_config = json.loads(args['model_config'])
        self.responses = {
            "artificial intelligence": "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. AI encompasses various subfields including machine learning, natural language processing, computer vision, and robotics. Modern AI systems can perform tasks such as understanding natural language, recognizing images, making decisions, and solving complex problems.",
            "language model": "A language model is a type of artificial intelligence model that's trained to understand and generate human language. Large Language Models (LLMs) like myself are trained on vast amounts of text data to predict the next word in a sequence, enabling them to generate coherent and contextually relevant text, answer questions, translate languages, and perform various text-based tasks.",
            "machine learning": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data, learn from it, and make predictions or decisions. Common types include supervised learning, unsupervised learning, and reinforcement learning.",
            "default": "As an AI language model, I'm designed to process and generate human-like text based on the input I receive. I can assist with a wide range of tasks including answering questions, providing explanations, generating creative content, and engaging in conversations on various topics. How else can I help you today?"
        }
        print(f"Initialized Simulated Llama model")
    
    def execute(self, requests):
        """
        Process inference requests.
        """
        responses = []
        
        for request in requests:
            # Get input tensors
            prompt = pb_utils.get_input_tensor_by_name(request, "prompt")
            prompt_data = prompt.as_numpy()
            
            # Decode prompt from bytes
            if prompt_data.dtype == np.object_:
                prompt_str = prompt_data[0][0].decode('utf-8')
            else:
                prompt_str = prompt_data[0][0]
            
            # Generate a relevant response based on the prompt
            generated_text = self._generate_response(prompt_str)
            
            # Create output tensor
            output_tensor = pb_utils.Tensor(
                "text_output", 
                np.array([[generated_text]], dtype=np.object_)
            )
            
            # Create and append response
            inference_response = pb_utils.InferenceResponse(
                output_tensors=[output_tensor]
            )
            responses.append(inference_response)
        
        return responses
    
    def _generate_response(self, prompt):
        """
        Generate a response based on the prompt keywords.
        """
        prompt_lower = prompt.lower()
        
        # Check for keywords in the prompt
        for key in self.responses:
            if key in prompt_lower:
                return self.responses[key]
        
        # If no keywords match, return the default response
        return self.responses["default"]
    
    def finalize(self):
        """
        Clean up resources when the model is unloaded.
        """
        print("Simulated Llama model unloaded") 
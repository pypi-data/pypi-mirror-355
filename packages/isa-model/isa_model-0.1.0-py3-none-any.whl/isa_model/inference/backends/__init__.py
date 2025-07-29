"""
Backend services for isa_model inference.

Three types of backend services:
1. Local Services: Services running locally (e.g., Ollama)
2. Container Services: Docker/K8s deployed services (e.g., Triton, vLLM)  
3. Third-party Services: External API services with wrappers
"""

from .base_backend_client import BaseBackendClient
from .triton_client import TritonBackendClient, TritonClient

# Local Services
from .local_services import OllamaBackendClient, LocalModelServerClient

# Container Services  
from .container_services import (
    VLLMBackendClient, 
    TensorFlowServingClient, 
    KubernetesServiceClient
)

# Third-party Services
from .third_party_services import (
    OpenAIClient,
    AnthropicClient, 
    CohereClient,
    AzureOpenAIClient,
    GoogleAIClient
)

__all__ = [
    # Base
    "BaseBackendClient",
    "TritonBackendClient",
    "TritonClient",  # Backward compatibility
    
    # Local Services
    "OllamaBackendClient",
    "LocalModelServerClient",
    
    # Container Services
    "VLLMBackendClient",
    "TensorFlowServingClient", 
    "KubernetesServiceClient",
    
    # Third-party Services
    "OpenAIClient",
    "AnthropicClient",
    "CohereClient", 
    "AzureOpenAIClient",
    "GoogleAIClient",
] 
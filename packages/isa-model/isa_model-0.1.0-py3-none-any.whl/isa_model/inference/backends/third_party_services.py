"""
Third-party Services Backend - External API services with wrappers.
Examples: OpenAI, Anthropic, Cohere, Google AI, Azure OpenAI
"""

import aiohttp
import json
from typing import Dict, Any, List, Optional
from .base_backend_client import BaseBackendClient


class OpenAIClient(BaseBackendClient):
    """Wrapper for OpenAI API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_completion(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate completion using OpenAI API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", 100),
                "temperature": kwargs.get("temperature", 0.7),
                **kwargs
            }
            async with session.post(
                f"{self.base_url}/completions", 
                json=payload, 
                headers=self.headers
            ) as response:
                return await response.json()
    
    async def generate_chat_completion(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate chat completion using OpenAI API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 100),
                "temperature": kwargs.get("temperature", 0.7),
                **kwargs
            }
            async with session.post(
                f"{self.base_url}/chat/completions", 
                json=payload, 
                headers=self.headers
            ) as response:
                return await response.json()
    
    async def generate_embeddings(self, model: str, input_text: str, **kwargs) -> Dict[str, Any]:
        """Generate embeddings using OpenAI API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "input": input_text,
                **kwargs
            }
            async with session.post(
                f"{self.base_url}/embeddings", 
                json=payload, 
                headers=self.headers
            ) as response:
                return await response.json()
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/models", headers=self.headers) as response:
                    return response.status == 200
        except Exception:
            return False


class AnthropicClient(BaseBackendClient):
    """Wrapper for Anthropic Claude API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    async def generate_chat_completion(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate chat completion using Anthropic API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 100),
                **kwargs
            }
            async with session.post(
                f"{self.base_url}/messages", 
                json=payload, 
                headers=self.headers
            ) as response:
                return await response.json()
    
    async def health_check(self) -> bool:
        """Check if Anthropic API is accessible"""
        try:
            # Anthropic doesn't have a models endpoint, so we'll just check the base URL
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, headers=self.headers) as response:
                    return response.status in [200, 404]  # 404 is also acceptable for base URL
        except Exception:
            return False


class CohereClient(BaseBackendClient):
    """Wrapper for Cohere API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.cohere.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_completion(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate completion using Cohere API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", 100),
                "temperature": kwargs.get("temperature", 0.7),
                **kwargs
            }
            async with session.post(
                f"{self.base_url}/generate", 
                json=payload, 
                headers=self.headers
            ) as response:
                return await response.json()
    
    async def generate_embeddings(self, model: str, texts: List[str], **kwargs) -> Dict[str, Any]:
        """Generate embeddings using Cohere API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "texts": texts,
                **kwargs
            }
            async with session.post(
                f"{self.base_url}/embed", 
                json=payload, 
                headers=self.headers
            ) as response:
                return await response.json()
    
    async def health_check(self) -> bool:
        """Check if Cohere API is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/check-api-key", headers=self.headers) as response:
                    return response.status == 200
        except Exception:
            return False


class AzureOpenAIClient(BaseBackendClient):
    """Wrapper for Azure OpenAI API"""
    
    def __init__(self, api_key: str, endpoint: str, api_version: str = "2023-12-01-preview"):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip('/')
        self.api_version = api_version
        self.headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
    
    async def generate_chat_completion(self, deployment_name: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate chat completion using Azure OpenAI API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 100),
                "temperature": kwargs.get("temperature", 0.7),
                **kwargs
            }
            url = f"{self.endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={self.api_version}"
            async with session.post(url, json=payload, headers=self.headers) as response:
                return await response.json()
    
    async def health_check(self) -> bool:
        """Check if Azure OpenAI API is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.endpoint}/openai/models?api-version={self.api_version}"
                async with session.get(url, headers=self.headers) as response:
                    return response.status == 200
        except Exception:
            return False


class GoogleAIClient(BaseBackendClient):
    """Wrapper for Google AI (Gemini) API"""
    
    def __init__(self, api_key: str, base_url: str = "https://generativelanguage.googleapis.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
    
    async def generate_completion(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate completion using Google AI API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": kwargs.get("max_tokens", 100),
                    "temperature": kwargs.get("temperature", 0.7),
                }
            }
            url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
            async with session.post(url, json=payload) as response:
                return await response.json()
    
    async def health_check(self) -> bool:
        """Check if Google AI API is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/models?key={self.api_key}"
                async with session.get(url) as response:
                    return response.status == 200
        except Exception:
            return False 
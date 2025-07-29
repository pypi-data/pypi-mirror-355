import httpx
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List
import json
import asyncio
import time

logger = logging.getLogger(__name__)

class ReplicateBackendClient:
    """Client for interacting with Replicate API"""
    
    def __init__(self, api_token: str, timeout: int = 120):
        """
        Initialize the Replicate client
        
        Args:
            api_token: Replicate API token
            timeout: Timeout for API calls in seconds
        """
        self.api_token = api_token
        self.api_base = "https://api.replicate.com/v1"
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {api_token}"
        }
        
        logger.info(f"Initialized Replicate client")
    
    async def post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a POST request to the Replicate API
        
        Args:
            endpoint: API endpoint (e.g., /predictions)
            payload: Request payload
            
        Returns:
            Response from the API
        """
        url = f"{self.api_base}{endpoint}"
        try:
            response = await self.client.post(url, json=payload, headers=self._headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = {}
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = {"status": e.response.status_code, "text": e.response.text}
                
            logger.error(f"Replicate API error: {error_detail}")
            raise ValueError(f"Replicate API error: {error_detail}")
        except Exception as e:
            logger.error(f"Error communicating with Replicate API: {e}")
            raise
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """
        Send a GET request to the Replicate API
        
        Args:
            endpoint: API endpoint (e.g., /predictions/{id})
            
        Returns:
            Response from the API
        """
        url = f"{self.api_base}{endpoint}"
        try:
            response = await self.client.get(url, headers=self._headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = {}
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = {"status": e.response.status_code, "text": e.response.text}
                
            logger.error(f"Replicate API error: {error_detail}")
            raise ValueError(f"Replicate API error: {error_detail}")
        except Exception as e:
            logger.error(f"Error communicating with Replicate API: {e}")
            raise
    
    async def create_prediction(self, model: str, version: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a prediction with Replicate
        
        Args:
            model: Model identifier (e.g., "meta/llama-3-8b-instruct")
            version: Model version or None to use latest
            input_data: Input data for the model
            
        Returns:
            Prediction result
        """
        model_identifier = f"{model}:{version}" if version else model
        
        payload = {
            "version": model_identifier,
            "input": input_data
        }
        
        # Create prediction
        prediction = await self.post("/predictions", payload)
        prediction_id = prediction["id"]
        
        # Poll for completion
        status = prediction["status"]
        max_attempts = 120  # 10 minutes with 5 second intervals
        attempts = 0
        
        while status in ["starting", "processing"] and attempts < max_attempts:
            await asyncio.sleep(5)
            prediction = await self.get(f"/predictions/{prediction_id}")
            status = prediction["status"]
            attempts += 1
        
        if status != "succeeded":
            error = prediction.get("error", "Unknown error")
            raise ValueError(f"Prediction failed: {error}")
        
        return prediction
    
    async def stream_prediction(self, model: str, version: str, input_data: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream a prediction from Replicate
        
        Args:
            model: Model identifier (e.g., "meta/llama-3-8b-instruct")
            version: Model version or None to use latest
            input_data: Input data for the model
            
        Yields:
            Output tokens from the model
        """
        # Set streaming in input data
        input_data["stream"] = True
        
        model_identifier = f"{model}:{version}" if version else model
        
        payload = {
            "version": model_identifier,
            "input": input_data
        }
        
        # Create prediction
        prediction = await self.post("/predictions", payload)
        prediction_id = prediction["id"]
        
        # Poll for the start of processing
        status = prediction["status"]
        while status in ["starting"]:
            await asyncio.sleep(1)
            prediction = await self.get(f"/predictions/{prediction_id}")
            status = prediction["status"]
        
        # Stream the output
        if status in ["processing", "succeeded"]:
            current_outputs = []
            last_output_len = 0
            max_attempts = 180  # 15 minutes with 5 second intervals
            attempts = 0
            
            while status in ["processing"] and attempts < max_attempts:
                prediction = await self.get(f"/predictions/{prediction_id}")
                status = prediction["status"]
                
                # Get outputs
                outputs = prediction.get("output", [])
                
                # If we have new tokens, yield them
                if isinstance(outputs, list) and len(outputs) > last_output_len:
                    for i in range(last_output_len, len(outputs)):
                        yield outputs[i]
                    last_output_len = len(outputs)
                
                await asyncio.sleep(0.5)
                attempts += 1
            
            # Final check for any remaining output
            if status == "succeeded":
                outputs = prediction.get("output", [])
                if isinstance(outputs, list) and len(outputs) > last_output_len:
                    for i in range(last_output_len, len(outputs)):
                        yield outputs[i]
        else:
            error = prediction.get("error", "Unknown error")
            raise ValueError(f"Prediction failed: {error}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose() 
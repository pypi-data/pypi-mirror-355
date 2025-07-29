import os
import json
import base64
import ollama
from typing import Dict, Any, Union
from tenacity import retry, stop_after_attempt, wait_exponential
from ...base_service import BaseService
from ...base_provider import BaseProvider
from app.config.config_manager import config_manager

logger = config_manager.get_logger(__name__)

class OllamaVisionService(BaseService):
    """Vision model service wrapper for Ollama using base64 encoded images"""
    
    def __init__(self, provider: 'BaseProvider', model_name: str = 'gemma3:4b'):
        super().__init__(provider, model_name)
        self.max_tokens = self.config.get('max_tokens', 1000)
        self.temperature = self.config.get('temperature', 0.7)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def analyze_image(self, image_data: Union[bytes, str], query: str) -> str:
        """分析图片并返回结果
        
        Args:
            image_data: 图片数据，可以是 bytes 或图片路径字符串
            query: 查询文本
            
        Returns:
            str: 分析结果
        """
        try:
            # 如果是文件路径，读取文件内容
            if isinstance(image_data, str):
                with open(image_data, 'rb') as f:
                    image_data = f.read()
            
            # 转换为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 使用 ollama 库直接调用
            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': query,
                    'images': [image_base64]
                }]
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            raise


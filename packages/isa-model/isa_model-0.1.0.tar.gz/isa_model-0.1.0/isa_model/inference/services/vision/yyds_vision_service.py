from typing import Dict, Any, Union
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from ...base_service import BaseService
from ...base_provider import BaseProvider
from .helpers.image_utils import compress_image, encode_image_to_base64
from app.config.config_manager import config_manager

logger = config_manager.get_logger(__name__)

class YYDSVisionService(BaseService):
    """Vision model service wrapper for YYDS"""
    
    def __init__(self, provider: 'BaseProvider', model_name: str):
        super().__init__(provider, model_name)
        # 初始化 AsyncOpenAI 客户端
        self._client = AsyncOpenAI(
            api_key=self.config.get('api_key'),
            base_url=self.config.get('base_url')
        )
        self.max_tokens = self.config.get('max_tokens', 1000)
        self.temperature = self.config.get('temperature', 0.7)
    
    @property
    def client(self) -> AsyncOpenAI:
        """获取底层的 OpenAI 客户端"""
        return self._client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def analyze_image(self, image_data: Union[bytes, str], query: str) -> str:
        """分析图片并返回结果
        
        Args:
            image_data: 图片数据，可以是 bytes 或已编码的 base64 字符串
            query: 查询文本
            
        Returns:
            str: 分析结果
        """
        try:
            # 处理图片数据
            if isinstance(image_data, bytes):
                # 压缩并编码图片
                compressed_image = compress_image(image_data)
                image_b64 = encode_image_to_base64(compressed_image)
            else:
                image_b64 = image_data
                
            # 移除可能存在的 base64 前缀
            if 'base64,' in image_b64:
                image_b64 = image_b64.split('base64,')[1]
                
            # 使用 AsyncOpenAI 客户端创建请求
            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                }],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            raise

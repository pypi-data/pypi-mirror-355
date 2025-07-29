from typing import Dict, Any
import tempfile
import os
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from ...base_service import BaseService
from ...base_provider import BaseProvider
from app.config.config_manager import config_manager

logger = config_manager.get_logger(__name__)

class YYDSAudioService(BaseService):
    """Audio model service wrapper for YYDS"""
    
    def __init__(self, provider: 'BaseProvider', model_name: str):
        super().__init__(provider, model_name)
        # 初始化 AsyncOpenAI 客户端
        self._client = AsyncOpenAI(
            api_key=self.config.get('api_key'),
            base_url=self.config.get('base_url')
        )
        self.language = self.config.get('language', None)
    
    @property
    def client(self) -> AsyncOpenAI:
        """获取底层的 OpenAI 客户端"""
        return self._client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def transcribe(self, audio_data: bytes) -> Dict[str, Any]:
        """转写音频数据
        
        Args:
            audio_data: 音频二进制数据
            
        Returns:
            Dict[str, Any]: 包含转写文本的字典
        """
        try:
            # 创建临时文件存储音频数据
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                # 以二进制模式打开文件用于 API 请求
                with open(temp_file.name, 'rb') as audio_file:
                    # 只在有效的 ISO-639-1 语言代码时包含 language 参数
                    params = {
                        'model': self.model_name,
                        'file': audio_file,
                    }
                    if self.language and isinstance(self.language, str):
                        params['language'] = self.language
                        
                    response = await self._client.audio.transcriptions.create(**params)
                    
                # 清理临时文件
                os.unlink(temp_file.name)
                
                # 返回包含转写文本的字典
                return {
                    "text": response.text
                }
                
        except Exception as e:
            logger.error(f"Error in audio transcription: {e}")
            raise

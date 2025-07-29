#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Replicate Vision服务
用于与Replicate API交互，支持图像生成和图像分析
"""

import os
import time
import uuid
import logging
from typing import Dict, Any, List, Optional, Union
import asyncio
import aiohttp
import replicate
import requests
from PIL import Image
from io import BytesIO

from isa_model.inference.services.base_service import BaseService
from isa_model.inference.providers.base_provider import BaseProvider
from isa_model.inference.base import ModelType

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReplicateVisionService(BaseService):
    """
    Replicate Vision服务，用于处理图像生成和分析
    """
    
    def __init__(self, provider: BaseProvider, model_name: str):
        """
        初始化Replicate Vision服务
        
        Args:
            provider: Replicate提供商实例
            model_name: Replicate模型ID (格式: 'username/model_name:version')
        """
        super().__init__(provider, model_name)
        self.api_token = provider.config.get("api_token", os.environ.get("REPLICATE_API_TOKEN"))
        self.client = replicate.Client(api_token=self.api_token)
        self.model_type = ModelType.VISION
        
        # 可选的默认配置
        self.guidance_scale = provider.config.get("guidance_scale", 7.5)
        self.num_inference_steps = provider.config.get("num_inference_steps", 30)
        
        # 生成的图像存储目录
        self.output_dir = "generated_images"
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def load(self) -> None:
        """
        加载模型（对于Replicate，这只是验证API令牌）
        """
        if not self.api_token:
            raise ValueError("缺少Replicate API令牌，请设置REPLICATE_API_TOKEN环境变量")
            
        # 验证令牌有效性
        try:
            self.client.api_token = self.api_token
            logger.info(f"Replicate Vision服务初始化成功，使用模型: {self.model_name}")
        except Exception as e:
            logger.error(f"Replicate初始化失败: {e}")
            raise
    
    async def generate_image(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用Replicate模型生成图像
        
        Args:
            input_data: 包含生成参数的字典
            
        Returns:
            包含生成图像URL的结果字典
        """
        try:
            # 设置默认参数
            if "guidance_scale" not in input_data and self.guidance_scale:
                input_data["guidance_scale"] = self.guidance_scale
                
            if "num_inference_steps" not in input_data and self.num_inference_steps:
                input_data["num_inference_steps"] = self.num_inference_steps
            
            # 运行模型（同步API调用）
            logger.info(f"开始使用模型 {self.model_name} 生成图像")
            
            # 转换成异步操作
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None, 
                lambda: replicate.run(self.model_name, input=input_data)
            )
            
            # 将结果转换为标准格式
            # 处理Replicate对象输出
            if hasattr(output, 'url'):
                urls = [output.url]
            elif isinstance(output, list) and all(hasattr(item, 'url') for item in output if item is not None):
                urls = [item.url for item in output if item is not None]
            else:
                # 兼容直接返回URL字符串的情况
                urls = output if isinstance(output, list) else [output]
            
            result = {
                "urls": urls,
                "metadata": {
                    "model": self.model_name,
                    "input": input_data
                }
            }
            
            logger.info(f"图像生成完成: {result['urls']}")
            return result
            
        except Exception as e:
            logger.error(f"图像生成失败: {e}")
            raise
    
    async def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        分析图像（用于支持视觉分析模型）
        
        Args:
            image_path: 图像路径或URL
            prompt: 分析提示
            
        Returns:
            分析结果字典
        """
        try:
            # 构建输入数据
            input_data = {
                "image": self._get_image_url(image_path),
                "prompt": prompt
            }
            
            # 运行模型
            logger.info(f"开始使用模型 {self.model_name} 分析图像")
            
            # 转换成异步操作
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None, 
                lambda: replicate.run(self.model_name, input=input_data)
            )
            
            result = {
                "text": output,
                "metadata": {
                    "model": self.model_name,
                    "input": input_data
                }
            }
            
            logger.info(f"图像分析完成")
            return result
            
        except Exception as e:
            logger.error(f"图像分析失败: {e}")
            raise
    
    async def generate_and_save(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成图像并保存到本地
        
        Args:
            input_data: 包含生成参数的字典
            
        Returns:
            包含生成图像URL和保存路径的结果字典
        """
        # 首先生成图像
        result = await self.generate_image(input_data)
        
        # 然后下载并保存
        saved_paths = []
        for i, url in enumerate(result["urls"]):
            # 生成唯一文件名
            timestamp = int(time.time())
            file_name = f"{self.output_dir}/{timestamp}_{uuid.uuid4().hex[:8]}_{i+1}.png"
            
            # 异步下载图像
            try:
                await self._download_image(url, file_name)
                saved_paths.append(file_name)
                logger.info(f"图像已保存至: {file_name}")
            except Exception as e:
                logger.error(f"保存图像失败: {e}")
        
        # 添加保存路径到结果
        result["saved_paths"] = saved_paths
        return result
    
    async def _download_image(self, url: str, save_path: str) -> None:
        """
        异步下载图像并保存
        
        Args:
            url: 图像URL
            save_path: 保存路径
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        img = Image.open(BytesIO(content))
                        img.save(save_path)
                    else:
                        logger.error(f"下载图像失败: HTTP {response.status}")
                        raise Exception(f"下载图像失败: HTTP {response.status}")
        except Exception as e:
            logger.error(f"下载图像时出错: {e}")
            raise
    
    def _get_image_url(self, image_path: str) -> str:
        """
        获取图像URL（如果提供的是本地路径，则上传到临时存储）
        
        Args:
            image_path: 图像路径或URL
            
        Returns:
            图像URL
        """
        # 如果已经是URL，直接返回
        if image_path.startswith(("http://", "https://")):
            return image_path
        
        # 否则，这是一个需要上传的本地文件
        # 注意：这里可以实现上传逻辑，但为简单起见，我们仅支持URL
        raise NotImplementedError("当前仅支持图像URL，不支持上传本地文件")
    
    async def unload(self) -> None:
        """卸载模型（对于Replicate API，这是一个无操作）"""
        logger.info(f"卸载Replicate Vision服务: {self.model_name}")
        # 没有需要清理的资源 
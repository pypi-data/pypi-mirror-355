from typing import Dict, List, Any, Optional
import aiohttp
import logging
import asyncio
from collections import OrderedDict
import os
import json
import hashlib
from pathlib import Path
from isa_model.inference.base import ModelType

logger = logging.getLogger(__name__)

class ModelCacheManager:
    """管理Triton服务器模型的加载/卸载，支持轮询模式"""
    
    def __init__(self, cache_size: int = 5, model_repository: str = "/models"):
        """
        初始化模型缓存管理器
        
        Args:
            cache_size: 最大缓存模型数量
            model_repository: 模型库路径
        """
        self.cache_size = cache_size
        self.model_repository = model_repository
        
        # LRU缓存使用OrderedDict
        self.model_cache = OrderedDict()
        
        # 服务器配置
        self.server_config = {
            "polling_enabled": True,  # 默认启用轮询模式（适合多模型场景）
            "triton_url": "localhost:8000",
            "openai_api_url": "localhost:9000"
        }
        
        # 模型类型映射
        self.model_type_map = {
            ModelType.LLM: "llm",
            ModelType.EMBEDDING: "embedding",
            ModelType.VISION: "vision",
            ModelType.RERANK: "rerank"
        }
        
        logger.info(f"初始化ModelCacheManager，缓存大小: {cache_size}，模型库: {model_repository}")
    
    async def detect_server_mode(self):
        """检测Triton服务器是否运行在轮询模式"""
        try:
            # 尝试加载任意模型以检测模式
            models = await self._get_repository_models()
            if not models:
                logger.warning("无法获取模型列表，无法检测服务器模式")
                return
                
            test_model = models[0]
            url = f"http://{self.server_config['triton_url']}/v2/repository/models/{test_model}/load"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    response_text = await response.text()
                    
                    if response.status == 503 and "polling is enabled" in response_text:
                        self.server_config["polling_enabled"] = True
                        logger.info("检测到Triton服务器运行在轮询模式（多模型模式）")
                    elif response.status == 200:
                        self.server_config["polling_enabled"] = False
                        logger.info("检测到Triton服务器运行在手动加载模式（单模型模式）")
                    else:
                        logger.warning(f"无法确定服务器模式，状态码: {response.status}")
        except Exception as e:
            logger.error(f"检测服务器模式时出错: {e}")
    
    async def load_model(self, model_name: str, model_type: ModelType) -> bool:
        """
        加载模型到Triton服务器
        
        Args:
            model_name: 模型名称
            model_type: 模型类型
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        # 如果是第一次加载，检测服务器模式
        if not hasattr(self, '_mode_detected'):
            await self.detect_server_mode()
            self._mode_detected = True
        
        if model_name in self.model_cache:
            # 模型已加载，移到LRU缓存末尾
            self.model_cache.move_to_end(model_name)
            logger.info(f"模型 {model_name} 已在缓存中，移至末尾")
            return True
        
        try:
            # 检查模型是否已加载到服务器
            is_loaded = await self._check_model_loaded(model_name)
            if is_loaded:
                logger.info(f"模型 {model_name} 已在服务器中加载")
                self.model_cache[model_name] = {
                    "type": model_type,
                    "load_time": asyncio.get_event_loop().time()
                }
                return True
            
            # 如果在轮询模式下，我们不能手动加载模型
            if self.server_config["polling_enabled"]:
                # 检查模型是否存在
                exists = await self._check_model_exists(model_name)
                if exists:
                    logger.warning(f"服务器在轮询模式下，无法手动加载模型 {model_name}，但模型存在")
                    # 我们假设模型将通过轮询加载
                    return True
                else:
                    logger.error(f"模型 {model_name} 不存在于服务器存储库中")
                    return False
            else:
                # 在非轮询模式下，可以手动加载
                # 如果缓存已满，卸载最少使用的模型
                if len(self.model_cache) >= self.cache_size:
                    lru_model, _ = self.model_cache.popitem(last=False)
                    await self._unload_from_triton(lru_model)
                    logger.info(f"从缓存中卸载LRU模型 {lru_model}")
                
                # 加载新模型
                success = await self._load_to_triton(model_name)
                if success:
                    self.model_cache[model_name] = {
                        "type": model_type,
                        "load_time": asyncio.get_event_loop().time()
                    }
                    logger.info(f"成功加载模型 {model_name}")
                    return True
                else:
                    logger.error(f"加载模型 {model_name} 失败")
                    return False
                
        except Exception as e:
            logger.error(f"加载模型 {model_name} 时出错: {e}")
            return False
    
    async def unload_model(self, model_name: str) -> bool:
        """卸载模型"""
        # 如果在轮询模式下，我们不能手动卸载模型
        if self.server_config["polling_enabled"]:
            logger.warning(f"服务器在轮询模式下，无法手动卸载模型 {model_name}")
            return True
        
        if model_name not in self.model_cache:
            logger.warning(f"模型 {model_name} 未在缓存中，无需卸载")
            return True
        
        try:
            # 卸载模型
            success = await self._unload_from_triton(model_name)
            if success:
                # 从缓存中移除
                self.model_cache.pop(model_name, None)
                logger.info(f"成功卸载模型 {model_name}")
                return True
            else:
                logger.error(f"卸载模型 {model_name} 失败")
                return False
                
        except Exception as e:
            logger.error(f"卸载模型 {model_name} 时出错: {e}")
            return False
    
    async def _load_to_triton(self, model_name: str) -> bool:
        """向Triton服务器发送加载模型请求"""
        try:
            logger.info(f"尝试加载模型 {model_name} 到Triton服务器")
            
            url = f"http://{self.server_config['triton_url']}/v2/repository/models/{model_name}/load"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        logger.info(f"成功加载模型 {model_name}")
                        return True
                    elif response.status == 400:
                        # 模型可能已加载
                        logger.info(f"模型 {model_name} 可能已加载: {response_text}")
                        return True
                    elif response.status == 503 and "polling is enabled" in response_text:
                        # 检测到轮询模式
                        self.server_config["polling_enabled"] = True
                        logger.warning(f"服务器在轮询模式下，无法手动加载模型: {response_text}")
                        # 检查模型是否存在
                        return await self._check_model_exists(model_name)
                    else:
                        logger.error(f"加载模型 {model_name} 失败: Status {response.status}, Response: {response_text}")
                        return False
                    
        except Exception as e:
            logger.error(f"向Triton API发送加载模型 {model_name} 请求时出错: {e}")
            return False
    
    async def _check_model_loaded(self, model_name: str) -> bool:
        """检查模型是否已加载"""
        try:
            url = f"http://{self.server_config['triton_url']}/v2/models/{model_name}/ready"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        logger.info(f"模型 {model_name} 已加载")
                        return True
                    else:
                        logger.info(f"模型 {model_name} 未加载，状态码: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"检查模型 {model_name} 是否加载时出错: {e}")
            return False
    
    async def _check_model_exists(self, model_name: str) -> bool:
        """检查模型是否存在于存储库中"""
        try:
            url = f"http://{self.server_config['triton_url']}/v2/repository/index"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    if response.status == 200:
                        models = await response.json()
                        model_names = [model["name"] for model in models]
                        exists = model_name in model_names
                        logger.info(f"模型 {model_name} {'存在' if exists else '不存在'}于存储库中")
                        logger.info(f"可用模型: {model_names}")
                        return exists
                    else:
                        logger.error(f"检查模型存在性失败: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"检查模型存在性时出错: {e}")
            return False
    
    async def _unload_from_triton(self, model_name: str) -> bool:
        """从Triton服务器卸载模型"""
        try:
            url = f"http://{self.server_config['triton_url']}/v2/repository/models/{model_name}/unload"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        logger.info(f"成功卸载模型 {model_name}")
                        return True
                    elif response.status == 503 and "polling is enabled" in response_text:
                        # 检测到轮询模式
                        self.server_config["polling_enabled"] = True
                        logger.warning(f"服务器在轮询模式下，无法手动卸载模型: {response_text}")
                        return True
                    else:
                        logger.error(f"卸载模型 {model_name} 失败: Status {response.status}, Response: {response_text}")
                        return False
        except Exception as e:
            logger.error(f"向Triton API发送卸载模型 {model_name} 请求时出错: {e}")
            return False
    
    def list_available_models(self, model_type: ModelType = None) -> List[str]:
        """
        列出可用模型
        
        Args:
            model_type: 按模型类型筛选
            
        Returns:
            模型名称列表
        """
        try:
            # 获取模型列表
            models = asyncio.run(self._get_repository_models())
            
            if not models:
                logger.warning("在存储库中未找到模型或无法连接到服务器")
                return []
            
            # 如果未指定模型类型，返回所有模型
            if model_type is None:
                return models
            
            # 基于命名约定的简单过滤器
            if model_type == ModelType.LLM:
                # 返回包含关键字的模型
                llm_keywords = ["llama", "mistral", "gemma", "qwen", "phi", "gpt", "falcon"]
                return [m for m in models if any(kw in m.lower() for kw in llm_keywords)]
            elif model_type == ModelType.EMBEDDING:
                embed_keywords = ["embed", "bge", "e5", "text-embedding"]
                return [m for m in models if any(kw in m.lower() for kw in embed_keywords)]
            elif model_type == ModelType.VISION:
                vision_keywords = ["clip", "vision", "multimodal", "image"]
                return [m for m in models if any(kw in m.lower() for kw in vision_keywords)]
            elif model_type == ModelType.RERANK:
                rerank_keywords = ["rerank", "cross-encoder"]
                return [m for m in models if any(kw in m.lower() for kw in rerank_keywords)]
            else:
                return []
                
        except Exception as e:
            logger.error(f"列出模型时出错: {e}")
            return []
    
    async def _get_repository_models(self) -> List[str]:
        """从Triton服务器获取模型列表"""
        try:
            url = f"http://{self.server_config['triton_url']}/v2/repository/index"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    if response.status == 200:
                        models = await response.json()
                        return [model["name"] for model in models]
                    else:
                        logger.error(f"获取模型失败: Status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"获取存储库模型时出错: {e}")
            return []
    
    async def get_openai_models(self) -> List[Dict[str, Any]]:
        """获取OpenAI兼容API中的可用模型"""
        try:
            url = f"http://{self.server_config['openai_api_url']}/v1/models"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"从OpenAI API获取到 {len(result.get('data', []))} 个模型")
                        return result.get("data", [])
                    else:
                        logger.error(f"获取OpenAI模型失败: Status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"获取OpenAI模型时出错: {e}")
            return [] 
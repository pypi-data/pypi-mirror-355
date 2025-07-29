from io import BytesIO
from PIL import Image
from typing import Union
import base64
from app.config.config_manager import config_manager

logger = config_manager.get_logger(__name__)

def compress_image(image_data: Union[bytes, BytesIO], max_size: int = 1024) -> bytes:
    """压缩图片以减小大小
    
    Args:
        image_data: 图片数据，可以是 bytes 或 BytesIO
        max_size: 最大尺寸（像素）
        
    Returns:
        bytes: 压缩后的图片数据
    """
    try:
        # 如果输入是 bytes，转换为 BytesIO
        if isinstance(image_data, bytes):
            image_data = BytesIO(image_data)
            
        img = Image.open(image_data)
        
        # 转换为 RGB 模式（如果需要）
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # 计算新尺寸，保持宽高比
        ratio = max_size / max(img.size)
        if ratio < 1:
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # 保存压缩后的图片
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        raise

def encode_image_to_base64(image_data: bytes) -> str:
    """将图片数据编码为 base64 字符串
    
    Args:
        image_data: 图片二进制数据
        
    Returns:
        str: base64 编码的字符串
    """
    try:
        return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image to base64: {e}")
        raise 
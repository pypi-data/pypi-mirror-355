from typing import Dict, Optional, List, Any
import logging
from pathlib import Path
from huggingface_hub import hf_hub_download, snapshot_download
from huggingface_hub.utils import HfHubHTTPError
from .model_storage import ModelStorage, LocalModelStorage
from .model_registry import ModelRegistry, ModelType, ModelCapability

logger = logging.getLogger(__name__)

class ModelManager:
    """Model management service for handling model downloads, versions, and caching"""
    
    def __init__(self, 
                 storage: Optional[ModelStorage] = None,
                 registry: Optional[ModelRegistry] = None):
        self.storage = storage or LocalModelStorage()
        self.registry = registry or ModelRegistry()
    
    async def get_model(self, 
                       model_id: str, 
                       repo_id: str,
                       model_type: ModelType,
                       capabilities: List[ModelCapability],
                       revision: Optional[str] = None,
                       force_download: bool = False) -> Path:
        """
        Get model files, downloading if necessary
        
        Args:
            model_id: Unique identifier for the model
            repo_id: Hugging Face repository ID
            model_type: Type of model (LLM, embedding, etc.)
            capabilities: List of model capabilities
            revision: Specific model version/tag
            force_download: Force re-download even if cached
            
        Returns:
            Path to the model files
        """
        # Check if model is already downloaded
        if not force_download:
            model_path = await self.storage.load_model(model_id)
            if model_path:
                logger.info(f"Using cached model {model_id}")
                return model_path
        
        try:
            # Download model files
            logger.info(f"Downloading model {model_id} from {repo_id}")
            model_dir = Path(f"./models/temp/{model_id}")
            model_dir.mkdir(parents=True, exist_ok=True)
            
            snapshot_download(
                repo_id=repo_id,
                revision=revision,
                local_dir=model_dir,
                local_dir_use_symlinks=False
            )
            
            # Save model and metadata
            metadata = {
                "repo_id": repo_id,
                "revision": revision,
                "downloaded_at": str(Path(model_dir).stat().st_mtime)
            }
            
            # Register model
            self.registry.register_model(
                model_id=model_id,
                model_type=model_type,
                capabilities=capabilities,
                metadata=metadata
            )
            
            # Save model files
            await self.storage.save_model(model_id, str(model_dir), metadata)
            
            return await self.storage.load_model(model_id)
            
        except HfHubHTTPError as e:
            logger.error(f"Failed to download model {model_id}: {e}")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all downloaded models with their metadata"""
        models = await self.storage.list_models()
        return [
            {
                "model_id": model_id,
                **metadata,
                **(self.registry.get_model_info(model_id) or {})
            }
            for model_id, metadata in models.items()
        ]
    
    async def remove_model(self, model_id: str) -> bool:
        """Remove a model and its metadata"""
        try:
            # Remove from storage
            storage_success = await self.storage.delete_model(model_id)
            
            # Unregister from registry
            registry_success = self.registry.unregister_model(model_id)
            
            return storage_success and registry_success
            
        except Exception as e:
            logger.error(f"Failed to remove model {model_id}: {e}")
            return False
    
    async def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        storage_info = await self.storage.get_metadata(model_id)
        registry_info = self.registry.get_model_info(model_id)
        
        if not storage_info and not registry_info:
            return None
            
        return {
            **(storage_info or {}),
            **(registry_info or {})
        }
    
    async def update_model(self, 
                          model_id: str, 
                          repo_id: str,
                          model_type: ModelType,
                          capabilities: List[ModelCapability],
                          revision: Optional[str] = None) -> bool:
        """Update a model to a new version"""
        try:
            return bool(await self.get_model(
                model_id=model_id,
                repo_id=repo_id,
                model_type=model_type,
                capabilities=capabilities,
                revision=revision,
                force_download=True
            ))
        except Exception as e:
            logger.error(f"Failed to update model {model_id}: {e}")
            return False 
"""
Model registry for managing model versions and stages.
"""

import os
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.entities.model_registry import ModelVersion as MlflowModelVersion

logger = logging.getLogger(__name__)


class ModelStage(str, Enum):
    """Stages of a model in the registry."""
    
    STAGING = "Staging"
    PRODUCTION = "Production"
    ARCHIVED = "Archived"
    NONE = "None"


class ModelVersion:
    """
    Model version representation.
    
    This class provides a wrapper around MLflow's ModelVersion entity
    with additional functionality.
    """
    
    def __init__(self, mlflow_model_version: MlflowModelVersion):
        """
        Initialize a model version.
        
        Args:
            mlflow_model_version: MLflow model version entity
        """
        self.mlflow_version = mlflow_model_version
        
    @property
    def name(self) -> str:
        """Get the model name."""
        return self.mlflow_version.name
        
    @property
    def version(self) -> str:
        """Get the version number."""
        return self.mlflow_version.version
        
    @property
    def stage(self) -> ModelStage:
        """Get the model stage."""
        return ModelStage(self.mlflow_version.current_stage)
        
    @property
    def description(self) -> str:
        """Get the model description."""
        return self.mlflow_version.description or ""
        
    @property
    def source(self) -> str:
        """Get the model source path."""
        return self.mlflow_version.source
        
    @property
    def run_id(self) -> str:
        """Get the run ID that created this model."""
        return self.mlflow_version.run_id
        
    @property
    def tags(self) -> Dict[str, str]:
        """Get the model tags."""
        return self.mlflow_version.tags or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model version to a dictionary.
        
        Returns:
            Dictionary representation of the model version
        """
        return {
            "name": self.name,
            "version": self.version,
            "stage": self.stage.value,
            "description": self.description,
            "source": self.source,
            "run_id": self.run_id,
            "tags": self.tags
        }


class ModelRegistry:
    """
    Registry for managing models and their versions.
    
    This class provides methods to register models, transition between
    stages, and retrieve models from the registry.
    
    Example:
        ```python
        # Create model registry
        registry = ModelRegistry(
            tracking_uri="http://localhost:5000",
            registry_uri="http://localhost:5000"
        )
        
        # Register a model
        version = registry.register_model(
            name="llama-7b-finetuned",
            source="path/to/model",
            description="Llama 7B finetuned on custom data"
        )
        
        # Transition to staging
        registry.transition_model_version_stage(
            name="llama-7b-finetuned",
            version=version,
            stage=ModelStage.STAGING
        )
        
        # Get the latest staging model
        staging_model = registry.get_latest_model_version(
            name="llama-7b-finetuned",
            stage=ModelStage.STAGING
        )
        ```
    """
    
    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        registry_uri: Optional[str] = None
    ):
        """
        Initialize the model registry.
        
        Args:
            tracking_uri: URI for MLflow tracking server
            registry_uri: URI for MLflow model registry
        """
        self.tracking_uri = tracking_uri or os.environ.get("MLFLOW_TRACKING_URI", "")
        self.registry_uri = registry_uri or os.environ.get("MLFLOW_REGISTRY_URI", "")
        
        self._setup_mlflow()
        self.client = MlflowClient(tracking_uri=self.tracking_uri, registry_uri=self.registry_uri)
        
    def _setup_mlflow(self) -> None:
        """Set up MLflow configuration."""
        if self.tracking_uri:
            mlflow.set_tracking_uri(self.tracking_uri)
            
        if self.registry_uri:
            mlflow.set_registry_uri(self.registry_uri)
    
    def create_registered_model(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Create a new registered model if it doesn't exist.
        
        Args:
            name: Name for the registered model
            tags: Tags for the registered model
            description: Description for the registered model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.create_registered_model(
                name=name,
                tags=tags,
                description=description
            )
            logger.info(f"Created registered model: {name}")
            return True
        except mlflow.exceptions.MlflowException as e:
            if "already exists" in str(e):
                logger.info(f"Model {name} already exists, skipping creation")
                return True
            logger.error(f"Failed to create registered model: {e}")
            return False
    
    def register_model(
        self,
        name: str,
        source: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Register a model with the registry.
        
        Args:
            name: Name for the registered model
            source: Source path of the model
            description: Description for the model version
            tags: Tags for the model version
            
        Returns:
            Version of the registered model or None if registration failed
        """
        # Ensure registered model exists
        self.create_registered_model(name)
        
        try:
            model_version = self.client.create_model_version(
                name=name,
                source=source,
                description=description,
                tags=tags
            )
            version = model_version.version
            logger.info(f"Registered model version: {name} v{version}")
            return version
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to register model: {e}")
            return None
    
    def get_model_version(
        self,
        name: str,
        version: str
    ) -> Optional[ModelVersion]:
        """
        Get a specific model version.
        
        Args:
            name: Name of the registered model
            version: Version of the model
            
        Returns:
            ModelVersion entity or None if not found
        """
        try:
            mlflow_version = self.client.get_model_version(name=name, version=version)
            return ModelVersion(mlflow_version)
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to get model version: {e}")
            return None
    
    def get_latest_model_version(
        self,
        name: str,
        stage: Optional[ModelStage] = None
    ) -> Optional[ModelVersion]:
        """
        Get the latest version of a model, optionally filtering by stage.
        
        Args:
            name: Name of the registered model
            stage: Stage to filter by
            
        Returns:
            Latest ModelVersion or None if not found
        """
        try:
            filter_string = f"name='{name}'"
            if stage:
                filter_string += f" AND stage='{stage.value}'"
                
            versions = self.client.search_model_versions(filter_string=filter_string)
            
            if not versions:
                logger.warning(f"No model versions found for {name}")
                return None
                
            # Sort by version number (newest first)
            sorted_versions = sorted(
                versions,
                key=lambda v: int(v.version),
                reverse=True
            )
            
            return ModelVersion(sorted_versions[0])
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to get latest model version: {e}")
            return None
    
    def list_model_versions(
        self,
        name: str,
        stage: Optional[ModelStage] = None
    ) -> List[ModelVersion]:
        """
        List all versions of a model, optionally filtering by stage.
        
        Args:
            name: Name of the registered model
            stage: Stage to filter by
            
        Returns:
            List of ModelVersion entities
        """
        try:
            filter_string = f"name='{name}'"
            if stage:
                filter_string += f" AND stage='{stage.value}'"
                
            mlflow_versions = self.client.search_model_versions(filter_string=filter_string)
            
            return [ModelVersion(v) for v in mlflow_versions]
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to list model versions: {e}")
            return []
    
    def list_registered_models(self) -> List[str]:
        """
        List all registered models in the registry.
        
        Returns:
            List of registered model names
        """
        try:
            models = self.client.list_registered_models()
            return [model.name for model in models]
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to list registered models: {e}")
            return []
    
    def transition_model_version_stage(
        self,
        name: str,
        version: str,
        stage: ModelStage,
        archive_existing_versions: bool = False
    ) -> Optional[ModelVersion]:
        """
        Transition a model version to a different stage.
        
        Args:
            name: Name of the registered model
            version: Version of the model
            stage: Stage to transition to
            archive_existing_versions: Whether to archive existing versions in the target stage
            
        Returns:
            Updated ModelVersion or None if transition failed
        """
        try:
            mlflow_version = self.client.transition_model_version_stage(
                name=name,
                version=version,
                stage=stage.value,
                archive_existing_versions=archive_existing_versions
            )
            logger.info(f"Transitioned model {name} v{version} to {stage.value}")
            return ModelVersion(mlflow_version)
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to transition model version: {e}")
            return None
    
    def update_model_version(
        self,
        name: str,
        version: str,
        description: Optional[str] = None
    ) -> Optional[ModelVersion]:
        """
        Update a model version's metadata.
        
        Args:
            name: Name of the registered model
            version: Version of the model
            description: New description for the model version
            
        Returns:
            Updated ModelVersion or None if update failed
        """
        try:
            mlflow_version = self.client.update_model_version(
                name=name,
                version=version,
                description=description
            )
            logger.info(f"Updated model version: {name} v{version}")
            return ModelVersion(mlflow_version)
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to update model version: {e}")
            return None
    
    def set_model_version_tag(
        self,
        name: str,
        version: str,
        key: str,
        value: str
    ) -> bool:
        """
        Set a tag on a model version.
        
        Args:
            name: Name of the registered model
            version: Version of the model
            key: Tag key
            value: Tag value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.set_model_version_tag(
                name=name,
                version=version,
                key=key,
                value=value
            )
            logger.debug(f"Set tag {key}={value} on model {name} v{version}")
            return True
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to set model version tag: {e}")
            return False
    
    def delete_model_version(
        self,
        name: str,
        version: str
    ) -> bool:
        """
        Delete a model version.
        
        Args:
            name: Name of the registered model
            version: Version of the model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_model_version(
                name=name,
                version=version
            )
            logger.info(f"Deleted model version: {name} v{version}")
            return True
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to delete model version: {e}")
            return False
    
    def delete_registered_model(
        self,
        name: str
    ) -> bool:
        """
        Delete a registered model and all its versions.
        
        Args:
            name: Name of the registered model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_registered_model(name=name)
            logger.info(f"Deleted registered model: {name}")
            return True
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to delete registered model: {e}")
            return False 
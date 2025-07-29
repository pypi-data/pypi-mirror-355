"""
MLflow manager for experiment tracking and model management.
"""

import os
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import mlflow
from mlflow.tracking import MlflowClient

logger = logging.getLogger(__name__)


class ExperimentType(str, Enum):
    """Types of experiments that can be tracked."""
    
    TRAINING = "training"
    FINETUNING = "finetuning"
    REINFORCEMENT_LEARNING = "rl"
    INFERENCE = "inference"
    EVALUATION = "evaluation"


class MLflowManager:
    """
    Manager class for MLflow operations.
    
    This class provides methods to set up MLflow, track experiments,
    log metrics, and manage models.
    
    Example:
        ```python
        # Initialize MLflow manager
        mlflow_manager = MLflowManager(
            tracking_uri="http://localhost:5000",
            artifact_uri="s3://bucket/artifacts"
        )
        
        # Set up experiment and start run
        with mlflow_manager.start_run(
            experiment_type=ExperimentType.FINETUNING,
            model_name="llama-7b"
        ) as run:
            # Log parameters
            mlflow_manager.log_params({
                "learning_rate": 2e-5,
                "batch_size": 8
            })
            
            # Train model...
            
            # Log metrics
            mlflow_manager.log_metrics({
                "accuracy": 0.95,
                "loss": 0.02
            })
            
            # Log model
            mlflow_manager.log_model(
                model_path="/path/to/model",
                name="finetuned-llama-7b"
            )
        ```
    """
    
    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        artifact_uri: Optional[str] = None,
        registry_uri: Optional[str] = None
    ):
        """
        Initialize the MLflow manager.
        
        Args:
            tracking_uri: URI for MLflow tracking server
            artifact_uri: URI for MLflow artifacts
            registry_uri: URI for MLflow model registry
        """
        self.tracking_uri = tracking_uri or os.environ.get("MLFLOW_TRACKING_URI", "")
        self.artifact_uri = artifact_uri or os.environ.get("MLFLOW_ARTIFACT_URI", "")
        self.registry_uri = registry_uri or os.environ.get("MLFLOW_REGISTRY_URI", "")
        
        self._setup_mlflow()
        self.client = MlflowClient(tracking_uri=self.tracking_uri, registry_uri=self.registry_uri)
        self.active_run = None
        
    def _setup_mlflow(self) -> None:
        """Set up MLflow configuration."""
        if self.tracking_uri:
            mlflow.set_tracking_uri(self.tracking_uri)
            logger.info(f"Set MLflow tracking URI to {self.tracking_uri}")
            
        if self.registry_uri:
            mlflow.set_registry_uri(self.registry_uri)
            logger.info(f"Set MLflow registry URI to {self.registry_uri}")
    
    def create_experiment(
        self,
        experiment_type: ExperimentType,
        model_name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a new experiment if it doesn't exist.
        
        Args:
            experiment_type: Type of experiment
            model_name: Name of the model
            tags: Tags for the experiment
            
        Returns:
            ID of the experiment
        """
        experiment_name = f"{model_name}_{experiment_type.value}"
        
        # Get experiment if exists, create if not
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(
                name=experiment_name,
                artifact_location=self.artifact_uri if self.artifact_uri else None,
                tags=tags
            )
            logger.info(f"Created new experiment: {experiment_name} (ID: {experiment_id})")
        else:
            experiment_id = experiment.experiment_id
            logger.info(f"Using existing experiment: {experiment_name} (ID: {experiment_id})")
            
        return experiment_id
    
    def start_run(
        self,
        experiment_type: ExperimentType,
        model_name: str,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        nested: bool = False
    ) -> mlflow.ActiveRun:
        """
        Start a new MLflow run.
        
        Args:
            experiment_type: Type of experiment
            model_name: Name of the model
            run_name: Name for the run
            tags: Tags for the run
            nested: Whether this is a nested run
            
        Returns:
            MLflow active run context
        """
        experiment_id = self.create_experiment(experiment_type, model_name)
        
        if not run_name:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            run_name = f"{model_name}_{experiment_type.value}_{timestamp}"
            
        self.active_run = mlflow.start_run(
            experiment_id=experiment_id,
            run_name=run_name,
            tags=tags,
            nested=nested
        )
        
        logger.info(f"Started MLflow run: {run_name} (ID: {self.active_run.info.run_id})")
        return self.active_run
    
    def end_run(self) -> None:
        """End the current MLflow run."""
        if mlflow.active_run():
            run_id = mlflow.active_run().info.run_id
            mlflow.end_run()
            logger.info(f"Ended MLflow run: {run_id}")
            self.active_run = None
    
    def log_params(self, params: Dict[str, Any]) -> None:
        """
        Log parameters to the current run.
        
        Args:
            params: Dictionary of parameters to log
        """
        if not mlflow.active_run():
            logger.warning("No active run. Parameters will not be logged.")
            return
            
        mlflow.log_params(params)
        logger.debug(f"Logged parameters: {params}")
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """
        Log metrics to the current run.
        
        Args:
            metrics: Dictionary of metrics to log
            step: Step value for the metrics
        """
        if not mlflow.active_run():
            logger.warning("No active run. Metrics will not be logged.")
            return
            
        mlflow.log_metrics(metrics, step=step)
        logger.debug(f"Logged metrics: {metrics}")
    
    def log_model(
        self,
        model_path: str,
        name: str,
        flavor: str = "pyfunc",
        **kwargs
    ) -> str:
        """
        Log a model to MLflow.
        
        Args:
            model_path: Path to the model
            name: Name for the logged model
            flavor: MLflow model flavor
            **kwargs: Additional arguments for model logging
            
        Returns:
            Path where the model is logged
        """
        if not mlflow.active_run():
            logger.warning("No active run. Model will not be logged.")
            return ""
            
        log_func = getattr(mlflow, f"log_{flavor}")
        if not log_func:
            logger.warning(f"Unsupported model flavor: {flavor}. Using pyfunc instead.")
            log_func = mlflow.pyfunc.log_model
            
        artifact_path = f"models/{name}"
        logged_model = log_func(
            artifact_path=artifact_path,
            path=model_path,
            **kwargs
        )
        
        logger.info(f"Logged model: {name} at {artifact_path}")
        return artifact_path
    
    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None) -> None:
        """
        Log an artifact to MLflow.
        
        Args:
            local_path: Local path to the artifact
            artifact_path: Path for the artifact in MLflow
        """
        if not mlflow.active_run():
            logger.warning("No active run. Artifact will not be logged.")
            return
            
        mlflow.log_artifact(local_path, artifact_path)
        logger.debug(f"Logged artifact: {local_path} to {artifact_path or 'root'}")
    
    def log_artifacts(self, local_dir: str, artifact_path: Optional[str] = None) -> None:
        """
        Log multiple artifacts to MLflow.
        
        Args:
            local_dir: Local directory containing artifacts
            artifact_path: Path for the artifacts in MLflow
        """
        if not mlflow.active_run():
            logger.warning("No active run. Artifacts will not be logged.")
            return
            
        mlflow.log_artifacts(local_dir, artifact_path)
        logger.debug(f"Logged artifacts from directory: {local_dir} to {artifact_path or 'root'}")
    
    def get_run(self, run_id: str) -> Optional[mlflow.entities.Run]:
        """
        Get a run by ID.
        
        Args:
            run_id: ID of the run
            
        Returns:
            MLflow run entity or None if not found
        """
        try:
            return self.client.get_run(run_id)
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to get run {run_id}: {e}")
            return None
    
    def search_runs(
        self,
        experiment_ids: List[str],
        filter_string: Optional[str] = None,
        max_results: int = 100
    ) -> List[mlflow.entities.Run]:
        """
        Search for runs in the given experiments.
        
        Args:
            experiment_ids: List of experiment IDs
            filter_string: Filter string for the search
            max_results: Maximum number of results to return
            
        Returns:
            List of MLflow run entities
        """
        try:
            return self.client.search_runs(
                experiment_ids=experiment_ids,
                filter_string=filter_string,
                max_results=max_results
            )
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to search runs: {e}")
            return []
            
    def get_experiment_id_by_name(self, experiment_name: str) -> Optional[str]:
        """
        Get experiment ID by name.
        
        Args:
            experiment_name: Name of the experiment
            
        Returns:
            Experiment ID or None if not found
        """
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment:
            return experiment.experiment_id
        return None
        
    def set_tracking_tag(self, key: str, value: str) -> None:
        """
        Set a tag for the current run.
        
        Args:
            key: Tag key
            value: Tag value
        """
        if not mlflow.active_run():
            logger.warning("No active run. Tag will not be set.")
            return
            
        mlflow.set_tag(key, value)
        logger.debug(f"Set tag: {key}={value}")
        
    def create_model_version(
        self,
        name: str,
        source: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Create a new model version in the registry.
        
        Args:
            name: Name of the registered model
            source: Source path of the model
            description: Description for the model version
            tags: Tags for the model version
            
        Returns:
            Version of the created model or None if creation failed
        """
        try:
            version = self.client.create_model_version(
                name=name,
                source=source,
                description=description,
                tags=tags
            )
            logger.info(f"Created model version: {name} v{version.version}")
            return version.version
        except mlflow.exceptions.MlflowException as e:
            logger.error(f"Failed to create model version: {e}")
            return None 
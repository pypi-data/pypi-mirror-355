"""
MLflow tracker for training workflows.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from contextlib import contextmanager

from .mlflow_manager import MLflowManager, ExperimentType
from .model_registry import ModelRegistry, ModelStage


logger = logging.getLogger(__name__)


class TrainingTracker:
    """
    Tracker for model training workflows.
    
    This class provides utilities to track model training using MLflow
    and register trained models in the model registry.
    
    Example:
        ```python
        # Initialize tracker
        tracker = TrainingTracker(
            tracking_uri="http://localhost:5000",
            registry_uri="http://localhost:5000"
        )
        
        # Start tracking training
        with tracker.track_training_run(
            model_name="llama-7b",
            training_params={
                "learning_rate": 2e-5,
                "batch_size": 8,
                "epochs": 3
            }
        ) as run_info:
            # Train the model...
            
            # Log metrics during training
            tracker.log_metrics({
                "train_loss": 0.1,
                "val_loss": 0.2
            })
            
            # After training completes
            model_path = "/path/to/trained_model"
            
            # Register the model
            tracker.register_trained_model(
                model_path=model_path,
                metrics={
                    "accuracy": 0.95,
                    "f1": 0.92
                },
                stage=ModelStage.STAGING
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
        Initialize the training tracker.
        
        Args:
            tracking_uri: URI for MLflow tracking server
            artifact_uri: URI for MLflow artifacts
            registry_uri: URI for MLflow model registry
        """
        self.mlflow_manager = MLflowManager(
            tracking_uri=tracking_uri,
            artifact_uri=artifact_uri,
            registry_uri=registry_uri
        )
        self.model_registry = ModelRegistry(
            tracking_uri=tracking_uri,
            registry_uri=registry_uri
        )
        self.current_run_info = {}
        
    @contextmanager
    def track_training_run(
        self,
        model_name: str,
        training_params: Dict[str, Any],
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        experiment_type: ExperimentType = ExperimentType.TRAINING
    ):
        """
        Track a training run with MLflow.
        
        Args:
            model_name: Name of the model being trained
            training_params: Parameters for the training run
            description: Description of the training run
            tags: Tags for the training run
            experiment_type: Type of experiment
            
        Yields:
            Dictionary with run information
        """
        run_info = {
            "model_name": model_name,
            "params": training_params,
            "metrics": {}
        }
        
        # Add description to tags if provided
        if tags is None:
            tags = {}
            
        if description:
            tags["description"] = description
            
        # Start the MLflow run
        with self.mlflow_manager.start_run(
            experiment_type=experiment_type,
            model_name=model_name,
            tags=tags
        ) as run:
            run_info["run_id"] = run.info.run_id
            run_info["experiment_id"] = run.info.experiment_id
            run_info["status"] = "running"
            
            # Save parameters
            self.mlflow_manager.log_params(training_params)
            
            self.current_run_info = run_info
            try:
                yield run_info
                # Mark as successful if no exceptions
                run_info["status"] = "completed"
            except Exception as e:
                # Mark as failed if exception occurred
                run_info["status"] = "failed"
                run_info["error"] = str(e)
                self.mlflow_manager.set_tracking_tag("error", str(e))
                raise
            finally:
                self.current_run_info = {}
                
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """
        Log metrics to the current run.
        
        Args:
            metrics: Dictionary of metrics to log
            step: Step value for the metrics
        """
        self.mlflow_manager.log_metrics(metrics, step)
        
        if self.current_run_info:
            if "metrics" not in self.current_run_info:
                self.current_run_info["metrics"] = {}
                
            # Only keep the latest metrics
            self.current_run_info["metrics"].update(metrics)
            
    def log_artifacts(self, local_dir: str, artifact_path: Optional[str] = None) -> None:
        """
        Log artifacts to the current run.
        
        Args:
            local_dir: Local directory containing artifacts
            artifact_path: Path for the artifacts in MLflow
        """
        self.mlflow_manager.log_artifacts(local_dir, artifact_path)
        
    def register_trained_model(
        self,
        model_path: str,
        metrics: Optional[Dict[str, float]] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        stage: Optional[ModelStage] = None,
        flavor: str = "pyfunc"
    ) -> Optional[str]:
        """
        Register a trained model with MLflow.
        
        Args:
            model_path: Path to the trained model
            metrics: Evaluation metrics for the model
            description: Description of the model
            tags: Tags for the model
            stage: Stage to register the model in
            flavor: MLflow model flavor
            
        Returns:
            Version of the registered model or None if registration failed
        """
        if not self.current_run_info:
            logger.warning("No active run. Model cannot be registered.")
            return None
            
        model_name = self.current_run_info.get("model_name")
        if not model_name:
            logger.warning("Model name not available in run info. Using generic name.")
            model_name = "unnamed_model"
            
        # Log final metrics if provided
        if metrics:
            self.log_metrics(metrics)
            
        # Prepare model tags
        if tags is None:
            tags = {}
            
        # Add run ID to tags
        tags["run_id"] = self.current_run_info.get("run_id", "")
        
        # Add metrics to tags
        for k, v in self.current_run_info.get("metrics", {}).items():
            tags[f"metric.{k}"] = str(v)
            
        # Log model to MLflow
        artifact_path = self.mlflow_manager.log_model(
            model_path=model_path,
            name=model_name,
            flavor=flavor
        )
        
        if not artifact_path:
            logger.error("Failed to log model to MLflow.")
            return None
            
        # Get model URI
        run_id = self.current_run_info.get("run_id")
        model_uri = f"runs:/{run_id}/{artifact_path}"
        
        # Register the model
        version = self.model_registry.register_model(
            name=model_name,
            source=model_uri,
            description=description,
            tags=tags
        )
        
        # Transition to the specified stage if provided
        if version and stage:
            self.model_registry.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage
            )
            
        return version 
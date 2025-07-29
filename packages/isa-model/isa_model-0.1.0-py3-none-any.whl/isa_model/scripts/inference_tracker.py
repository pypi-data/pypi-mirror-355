"""
MLflow tracker for inference workflows.
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from contextlib import contextmanager

from .mlflow_manager import MLflowManager, ExperimentType
from .model_registry import ModelRegistry, ModelStage, ModelVersion


logger = logging.getLogger(__name__)


class InferenceTracker:
    """
    Tracker for model inference workflows.
    
    This class provides utilities to track model inference using MLflow,
    including performance metrics and input/output logging.
    
    Example:
        ```python
        # Initialize tracker
        tracker = InferenceTracker(
            tracking_uri="http://localhost:5000"
        )
        
        # Get model from registry
        model_version = tracker.get_production_model("llama-7b")
        
        # Track inference
        with tracker.track_inference(
            model_name="llama-7b",
            model_version=model_version.version
        ):
            # Start timer
            start_time = time.time()
            
            # Generate text
            output = model.generate(prompt)
            
            # Log inference
            tracker.log_inference(
                input=prompt,
                output=output,
                latency_ms=(time.time() - start_time) * 1000
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
        Initialize the inference tracker.
        
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
        self.inference_samples = []
        
    def get_production_model(self, model_name: str) -> Optional[ModelVersion]:
        """
        Get the production version of a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Production ModelVersion or None if not found
        """
        return self.model_registry.get_latest_model_version(
            name=model_name,
            stage=ModelStage.PRODUCTION
        )
        
    def get_staging_model(self, model_name: str) -> Optional[ModelVersion]:
        """
        Get the staging version of a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Staging ModelVersion or None if not found
        """
        return self.model_registry.get_latest_model_version(
            name=model_name,
            stage=ModelStage.STAGING
        )
        
    @contextmanager
    def track_inference(
        self,
        model_name: str,
        model_version: Optional[str] = None,
        batch_size: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Track model inference with MLflow.
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            batch_size: Batch size for inference
            tags: Tags for the run
            
        Yields:
            Dictionary with run information
        """
        run_info = {
            "model_name": model_name,
            "model_version": model_version,
            "batch_size": batch_size,
            "start_time": time.time(),
            "metrics": {}
        }
        
        # Prepare tags
        if tags is None:
            tags = {}
            
        tags["model_name"] = model_name
        if model_version:
            tags["model_version"] = model_version
            
        if batch_size:
            tags["batch_size"] = str(batch_size)
            
        # Start the MLflow run
        with self.mlflow_manager.start_run(
            experiment_type=ExperimentType.INFERENCE,
            model_name=model_name,
            tags=tags
        ) as run:
            run_info["run_id"] = run.info.run_id
            run_info["experiment_id"] = run.info.experiment_id
            
            # Reset inference samples
            self.inference_samples = []
            
            self.current_run_info = run_info
            try:
                yield run_info
                
                # Calculate and log summary metrics
                self._log_summary_metrics()
                
                # Save inference samples
                if self.inference_samples:
                    self._save_inference_samples()
                    
            finally:
                run_info["end_time"] = time.time()
                run_info["duration"] = run_info["end_time"] - run_info["start_time"]
                
                # Log duration
                self.mlflow_manager.log_metrics({
                    "duration_seconds": run_info["duration"]
                })
                
                self.current_run_info = {}
                
    def log_inference(
        self,
        input: str,
        output: str,
        latency_ms: Optional[float] = None,
        token_count: Optional[int] = None,
        tokens_per_second: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an inference sample.
        
        Args:
            input: Input prompt
            output: Generated output
            latency_ms: Latency in milliseconds
            token_count: Number of tokens generated
            tokens_per_second: Tokens per second
            metadata: Additional metadata
        """
        if not self.current_run_info:
            logger.warning("No active run. Inference will not be logged.")
            return
            
        sample = {
            "input": input,
            "output": output,
            "timestamp": time.time()
        }
        
        if latency_ms is not None:
            sample["latency_ms"] = latency_ms
            
        if token_count is not None:
            sample["token_count"] = token_count
            
        if tokens_per_second is not None:
            sample["tokens_per_second"] = tokens_per_second
            
        if metadata:
            sample["metadata"] = metadata
            
        self.inference_samples.append(sample)
        
        # Log individual metrics
        metrics = {}
        if latency_ms is not None:
            metrics["latency_ms"] = latency_ms
            
        if token_count is not None:
            metrics["token_count"] = token_count
            
        if tokens_per_second is not None:
            metrics["tokens_per_second"] = tokens_per_second
            
        if metrics:
            self.mlflow_manager.log_metrics(metrics)
    
    def _log_summary_metrics(self) -> None:
        """Log summary metrics based on all inference samples."""
        if not self.inference_samples:
            return
            
        latencies = [s.get("latency_ms") for s in self.inference_samples if "latency_ms" in s]
        token_counts = [s.get("token_count") for s in self.inference_samples if "token_count" in s]
        tokens_per_second = [s.get("tokens_per_second") for s in self.inference_samples if "tokens_per_second" in s]
        
        metrics = {
            "inference_count": len(self.inference_samples)
        }
        
        if latencies:
            metrics["avg_latency_ms"] = sum(latencies) / len(latencies)
            metrics["min_latency_ms"] = min(latencies)
            metrics["max_latency_ms"] = max(latencies)
            
        if token_counts:
            metrics["avg_token_count"] = sum(token_counts) / len(token_counts)
            metrics["total_tokens"] = sum(token_counts)
            
        if tokens_per_second:
            metrics["avg_tokens_per_second"] = sum(tokens_per_second) / len(tokens_per_second)
            
        self.mlflow_manager.log_metrics(metrics)
        
    def _save_inference_samples(self) -> None:
        """Save inference samples as an artifact."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(self.inference_samples, f, indent=2)
            temp_path = f.name
            
        self.mlflow_manager.log_artifact(temp_path, "inference_samples.json")
        
        try:
            os.remove(temp_path)
        except:
            pass 
"""
MLflow Gateway module for IsA Model.
Replaces the custom adapter with industry-standard MLflow Gateway.
"""

from .start_gateway import start_mlflow_gateway

__all__ = ["start_mlflow_gateway"] 
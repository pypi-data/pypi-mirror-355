"""
Inference module for isA_Model

File: isa_model/inference/__init__.py
This module provides the main inference components for the IsA Model system.
"""

from .ai_factory import AIFactory
from .base import ModelType, Capability, RoutingStrategy

__all__ = ["AIFactory", "ModelType", "Capability", "RoutingStrategy"] 
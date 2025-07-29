"""
LlamaFactory interface module.

This module provides the main interface for using LlamaFactory functionality.
"""

import os
import logging
from typing import Optional, Dict, Any, Union, List

from .config import (
    LlamaFactoryConfig,
    SFTConfig,
    RLConfig,
    DPOConfig,
    TrainingStrategy,
    DatasetFormat,
    create_default_config
)
from .trainer import LlamaFactoryTrainer
from .rl import LlamaFactoryRL
from .data_adapter import DataAdapterFactory


logger = logging.getLogger(__name__)


class LlamaFactory:
    """
    Main interface class for LlamaFactory operations.
    
    This class provides a simplified interface to the LlamaFactory functionality
    for fine-tuning and reinforcement learning.
    
    Example for fine-tuning:
        ```python
        # Create a LlamaFactory instance
        factory = LlamaFactory()
        
        # Fine-tune a model
        model_path = factory.finetune(
            model_path="meta-llama/Llama-2-7b-hf",
            train_data="path/to/data.json",
            val_data="path/to/val_data.json",  # Optional
            output_dir="path/to/output",
            dataset_format=DatasetFormat.ALPACA,
            use_lora=True,
            num_epochs=3
        )
        ```
        
    Example for RL training:
        ```python
        # Create a LlamaFactory instance
        factory = LlamaFactory()
        
        # Train with DPO
        model_path = factory.dpo(
            model_path="meta-llama/Llama-2-7b-hf",
            train_data="path/to/preferences.json",
            output_dir="path/to/output",
            reference_model="meta-llama/Llama-2-7b-hf",  # Optional
            beta=0.1
        )
        ```
    """
    
    def __init__(self, base_output_dir: Optional[str] = None):
        """
        Initialize the LlamaFactory interface.
        
        Args:
            base_output_dir: Base directory for outputs
        """
        self.base_output_dir = base_output_dir or os.path.join(os.getcwd(), "training_outputs")
        os.makedirs(self.base_output_dir, exist_ok=True)
        
    def _get_output_dir(self, name: str, output_dir: Optional[str] = None) -> str:
        """
        Get the output directory for training.
        
        Args:
            name: Name for the output directory
            output_dir: Optional specific output directory
            
        Returns:
            Output directory path
        """
        if output_dir:
            return output_dir
            
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.base_output_dir, f"{name}_{timestamp}")
    
    def finetune(
        self,
        model_path: str,
        train_data: str,
        val_data: Optional[str] = None,
        output_dir: Optional[str] = None,
        dataset_format: DatasetFormat = DatasetFormat.ALPACA,
        use_lora: bool = True,
        batch_size: int = 8,
        num_epochs: int = 3,
        learning_rate: float = 2e-5,
        lora_rank: int = 8,
        lora_alpha: int = 16,
        max_length: int = 1024,
        **kwargs
    ) -> str:
        """
        Fine-tune a model using supervised learning.
        
        Args:
            model_path: Path or name of the base model
            train_data: Path to the training data
            val_data: Path to the validation data (optional)
            output_dir: Directory to save outputs
            dataset_format: Format of the dataset
            use_lora: Whether to use LoRA for training
            batch_size: Training batch size
            num_epochs: Number of training epochs
            learning_rate: Learning rate
            lora_rank: LoRA rank parameter
            lora_alpha: LoRA alpha parameter
            max_length: Maximum sequence length
            **kwargs: Additional parameters for SFTConfig
            
        Returns:
            Path to the trained model
        """
        # Check if data conversion is needed and convert
        adapter = DataAdapterFactory.create_adapter(dataset_format)
        converted_train_data = adapter.convert_data(train_data)
        converted_val_data = adapter.convert_data(val_data) if val_data else None
        
        # Create configuration
        output_dir = self._get_output_dir("sft", output_dir)
        config = SFTConfig(
            model_path=model_path,
            train_file=converted_train_data,
            val_file=converted_val_data,
            output_dir=output_dir,
            use_lora=use_lora,
            batch_size=batch_size,
            num_epochs=num_epochs,
            learning_rate=learning_rate,
            lora_rank=lora_rank,
            lora_alpha=lora_alpha,
            max_length=max_length,
            dataset_format=dataset_format,
            **kwargs
        )
        
        # Initialize and run trainer
        trainer = LlamaFactoryTrainer(config)
        model_dir = trainer.train()
        
        # Export model if using LoRA
        if use_lora:
            model_dir = trainer.export_model()
            
        return model_dir
    
    def rlhf(
        self,
        model_path: str,
        reward_model: str,
        train_data: str,
        output_dir: Optional[str] = None,
        use_lora: bool = True,
        batch_size: int = 4,
        num_epochs: int = 1,
        learning_rate: float = 1e-5,
        kl_coef: float = 0.1,
        **kwargs
    ) -> str:
        """
        Train a model with RLHF (Reinforcement Learning from Human Feedback).
        
        Args:
            model_path: Path or name of the base model
            reward_model: Path to the reward model
            train_data: Path to the training data
            output_dir: Directory to save outputs
            use_lora: Whether to use LoRA for training
            batch_size: Training batch size
            num_epochs: Number of training epochs
            learning_rate: Learning rate
            kl_coef: KL coefficient for PPO
            **kwargs: Additional parameters for RLConfig
            
        Returns:
            Path to the trained model
        """
        # Create configuration
        output_dir = self._get_output_dir("rlhf", output_dir)
        config = RLConfig(
            model_path=model_path,
            reward_model=reward_model,
            train_file=train_data,
            output_dir=output_dir,
            use_lora=use_lora,
            batch_size=batch_size,
            num_epochs=num_epochs,
            learning_rate=learning_rate,
            kl_coef=kl_coef,
            **kwargs
        )
        
        # Initialize and run RL trainer
        rl_trainer = LlamaFactoryRL(config)
        model_dir = rl_trainer.train()
        
        # Export model if using LoRA
        if use_lora:
            model_dir = rl_trainer.export_model()
            
        return model_dir
    
    def dpo(
        self,
        model_path: str,
        train_data: str,
        val_data: Optional[str] = None,
        reference_model: Optional[str] = None,
        output_dir: Optional[str] = None,
        use_lora: bool = True,
        batch_size: int = 4,
        num_epochs: int = 3,
        learning_rate: float = 5e-6,
        beta: float = 0.1,
        **kwargs
    ) -> str:
        """
        Train a model with DPO (Direct Preference Optimization).
        
        Args:
            model_path: Path or name of the base model
            train_data: Path to the training data
            val_data: Path to the validation data (optional)
            reference_model: Path to the reference model (optional)
            output_dir: Directory to save outputs
            use_lora: Whether to use LoRA for training
            batch_size: Training batch size
            num_epochs: Number of training epochs
            learning_rate: Learning rate
            beta: DPO beta parameter
            **kwargs: Additional parameters for DPOConfig
            
        Returns:
            Path to the trained model
        """
        # Create configuration
        output_dir = self._get_output_dir("dpo", output_dir)
        config = DPOConfig(
            model_path=model_path,
            train_file=train_data,
            val_file=val_data,
            reference_model=reference_model,
            output_dir=output_dir,
            use_lora=use_lora,
            batch_size=batch_size,
            num_epochs=num_epochs,
            learning_rate=learning_rate,
            beta=beta,
            **kwargs
        )
        
        # Initialize and run DPO trainer
        dpo_trainer = LlamaFactoryRL(config)
        model_dir = dpo_trainer.train()
        
        # Export model if using LoRA
        if use_lora:
            model_dir = dpo_trainer.export_model()
            
        return model_dir
    
    def train_reward_model(
        self,
        model_path: str,
        train_data: str,
        val_data: Optional[str] = None,
        output_dir: Optional[str] = None,
        use_lora: bool = True,
        batch_size: int = 8,
        num_epochs: int = 3,
        learning_rate: float = 1e-5,
        **kwargs
    ) -> str:
        """
        Train a reward model for RLHF.
        
        Args:
            model_path: Path or name of the base model
            train_data: Path to the training data with preferences
            val_data: Path to the validation data (optional)
            output_dir: Directory to save outputs
            use_lora: Whether to use LoRA for training
            batch_size: Training batch size
            num_epochs: Number of training epochs
            learning_rate: Learning rate
            **kwargs: Additional parameters for RLConfig
            
        Returns:
            Path to the trained reward model
        """
        # Create temporary RL config
        output_dir = self._get_output_dir("reward_model", output_dir)
        config = RLConfig(
            model_path=model_path,
            train_file=train_data,
            output_dir=output_dir,
            use_lora=use_lora,
            batch_size=batch_size,
            num_epochs=num_epochs,
            learning_rate=learning_rate,
            **kwargs
        )
        
        # Initialize RL trainer and train reward model
        rl_trainer = LlamaFactoryRL(config)
        model_dir = rl_trainer.train_reward_model()
        
        # Export model if using LoRA
        if use_lora:
            model_dir = rl_trainer.export_model()
            
        return model_dir 
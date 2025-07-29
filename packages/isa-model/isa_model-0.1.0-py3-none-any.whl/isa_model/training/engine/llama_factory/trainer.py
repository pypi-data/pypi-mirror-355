"""
LlamaFactory training implementation.
"""

import os
import json
import logging
import subprocess
from typing import Dict, List, Optional, Union, Any

from .config import (
    LlamaFactoryConfig,
    SFTConfig,
    TrainingStrategy,
    DatasetFormat
)

logger = logging.getLogger(__name__)


class LlamaFactoryTrainer:
    """
    Trainer class for LlamaFactory fine-tuning operations.
    
    This class provides methods to fine-tune language models using LlamaFactory.
    It supports supervised fine-tuning (SFT) and manages the execution of the
    training process.
    
    Example:
        ```python
        # Create configuration
        config = SFTConfig(
            model_path="meta-llama/Llama-2-7b-hf",
            train_file="path/to/data.json",
            batch_size=8,
            num_epochs=3
        )
        
        # Initialize and run trainer
        trainer = LlamaFactoryTrainer(config)
        trainer.train()
        ```
    """
    
    def __init__(self, config: LlamaFactoryConfig):
        """
        Initialize the LlamaFactory trainer.
        
        Args:
            config: Configuration for training
        """
        self.config = config
        self._validate_config()
        self.output_dir = config.output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not self.config.model_path:
            raise ValueError("Model path must be specified")
            
        if isinstance(self.config, SFTConfig) and not self.config.train_file:
            raise ValueError("Training file must be specified for SFT")
    
    def _prepare_training_args(self) -> Dict[str, Any]:
        """
        Prepare training arguments for LlamaFactory CLI.
        
        Returns:
            Dictionary of training arguments
        """
        base_args = self.config.to_dict()
        
        # Add stage-specific args
        if self.config.strategy == TrainingStrategy.SUPERVISED_FINETUNING:
            base_args["stage"] = "sft"
        
        # Handle LoRA settings
        if self.config.use_lora:
            base_args["lora_target"] = "q_proj,v_proj"
            
        return base_args
    
    def _save_training_args(self, args: Dict[str, Any]) -> str:
        """
        Save training arguments to a JSON file.
        
        Args:
            args: Training arguments
            
        Returns:
            Path to the saved JSON file
        """
        args_file = os.path.join(self.output_dir, "train_args.json")
        with open(args_file, "w") as f:
            json.dump(args, f, indent=2)
        return args_file
    
    def _build_command(self, args_file: str) -> List[str]:
        """
        Build the command to run LlamaFactory.
        
        Args:
            args_file: Path to the arguments file
            
        Returns:
            Command list for subprocess
        """
        return [
            "python", "-m", "llmtuner.cli.sft",
            "--cfg_file", args_file
        ]
    
    def train(self) -> str:
        """
        Run the training process.
        
        Returns:
            Path to the output directory with trained model
        """
        args = self._prepare_training_args()
        args_file = self._save_training_args(args)
        
        cmd = self._build_command(args_file)
        logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            subprocess.run(
                cmd,
                check=True,
                text=True,
                stderr=subprocess.STDOUT
            )
            logger.info(f"Training completed successfully. Model saved to {self.output_dir}")
            return self.output_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"Training failed with error: {e}")
            raise RuntimeError(f"LlamaFactory training failed: {e}")
            
    def export_model(self, output_path: Optional[str] = None) -> str:
        """
        Export the trained model.
        
        Args:
            output_path: Path to save the exported model
            
        Returns:
            Path to the exported model
        """
        if output_path is None:
            output_path = os.path.join(self.output_dir, "exported")
            
        os.makedirs(output_path, exist_ok=True)
        
        # If using LoRA, need to merge weights
        if self.config.use_lora:
            cmd = [
                "python", "-m", "llmtuner.cli.merge",
                "--model_name_or_path", self.config.model_path,
                "--adapter_name_or_path", self.output_dir,
                "--output_dir", output_path
            ]
            
            subprocess.run(cmd, check=True, text=True)
            logger.info(f"Model exported successfully to {output_path}")
        else:
            # Just copy the model
            import shutil
            shutil.copytree(self.output_dir, output_path, dirs_exist_ok=True)
            
        return output_path 
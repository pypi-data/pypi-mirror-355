"""
LlamaFactory reinforcement learning implementation.
"""

import os
import json
import logging
import subprocess
from typing import Dict, List, Optional, Union, Any, Tuple

from .config import (
    LlamaFactoryConfig,
    RLConfig,
    DPOConfig,
    TrainingStrategy
)

logger = logging.getLogger(__name__)


class LlamaFactoryRL:
    """
    Reinforcement Learning class for LlamaFactory.
    
    This class provides methods to train language models using reinforcement
    learning approaches such as RLHF (PPO) and DPO.
    
    Example:
        ```python
        # Create RL configuration
        config = RLConfig(
            model_path="meta-llama/Llama-2-7b-hf",
            reward_model="reward-model-path",
            train_file="path/to/data.json",
            batch_size=8
        )
        
        # Initialize and run RL training
        rl_trainer = LlamaFactoryRL(config)
        rl_trainer.train()
        ```
        
    For DPO:
        ```python
        # Create DPO configuration
        config = DPOConfig(
            model_path="meta-llama/Llama-2-7b-hf",
            train_file="path/to/preferences.json",
            reference_model="meta-llama/Llama-2-7b-hf",  # Optional
            batch_size=4
        )
        
        # Initialize and run DPO training
        dpo_trainer = LlamaFactoryRL(config)
        dpo_trainer.train()
        ```
    """
    
    def __init__(self, config: Union[RLConfig, DPOConfig]):
        """
        Initialize the LlamaFactory RL trainer.
        
        Args:
            config: Configuration for RL training
        """
        self.config = config
        self._validate_config()
        self.output_dir = config.output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not self.config.model_path:
            raise ValueError("Model path must be specified")
            
        if isinstance(self.config, RLConfig):
            if not self.config.reward_model:
                raise ValueError("Reward model must be specified for RLHF")
            if not self.config.train_file:
                raise ValueError("Training file must be specified for RLHF")
                
        if isinstance(self.config, DPOConfig) and not self.config.train_file:
            raise ValueError("Training file must be specified for DPO")
    
    def _prepare_training_args(self) -> Dict[str, Any]:
        """
        Prepare training arguments for LlamaFactory CLI.
        
        Returns:
            Dictionary of training arguments
        """
        base_args = self.config.to_dict()
        
        # Add stage-specific args
        if self.config.strategy == TrainingStrategy.REINFORCEMENT_LEARNING:
            base_args["stage"] = "rm" if self._is_reward_model_training() else "ppo"
        elif self.config.strategy == TrainingStrategy.PREFERENCE_OPTIMIZATION:
            base_args["stage"] = "dpo"
            
        # Handle LoRA settings
        if self.config.use_lora:
            base_args["lora_target"] = "q_proj,v_proj"
            
        return base_args
    
    def _is_reward_model_training(self) -> bool:
        """
        Check if we're training a reward model for RLHF.
        
        Returns:
            True if reward model training, False otherwise
        """
        # This is a placeholder. In a real implementation, 
        # you'd have a separate flag in the config
        return False
        
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
        cmd_module = "llmtuner.cli.ppo"
        if self.config.strategy == TrainingStrategy.PREFERENCE_OPTIMIZATION:
            cmd_module = "llmtuner.cli.dpo"
        elif self._is_reward_model_training():
            cmd_module = "llmtuner.cli.rm"
            
        return [
            "python", "-m", cmd_module,
            "--cfg_file", args_file
        ]
    
    def train(self) -> str:
        """
        Run the RL training process.
        
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
            logger.info(f"RL training completed successfully. Model saved to {self.output_dir}")
            return self.output_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"RL training failed with error: {e}")
            raise RuntimeError(f"LlamaFactory RL training failed: {e}")
    
    def train_reward_model(self) -> str:
        """
        Train a reward model for RLHF.
        
        Returns:
            Path to the trained reward model
        """
        # Create temporary config for reward model training
        reward_config = RLConfig(
            model_path=self.config.model_path,
            output_dir=os.path.join(self.output_dir, "reward_model"),
            train_file=self.config.train_file,
            batch_size=self.config.batch_size,
            num_epochs=self.config.num_epochs,
            learning_rate=self.config.learning_rate
        )
        
        # Set as reward model training
        # In a real implementation, you'd have a proper flag in the config
        self.config = reward_config
        
        args = self._prepare_training_args()
        args_file = self._save_training_args(args)
        
        cmd = [
            "python", "-m", "llmtuner.cli.rm",
            "--cfg_file", args_file
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            subprocess.run(
                cmd,
                check=True,
                text=True,
                stderr=subprocess.STDOUT
            )
            logger.info(f"Reward model training completed successfully. Model saved to {reward_config.output_dir}")
            return reward_config.output_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"Reward model training failed with error: {e}")
            raise RuntimeError(f"LlamaFactory reward model training failed: {e}")
            
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
"""
Configuration classes for LlamaFactory training and RL.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum
import os
from pathlib import Path


class TrainingStrategy(str, Enum):
    """Training strategies supported by LlamaFactory."""
    
    SUPERVISED_FINETUNING = "sft"
    REINFORCEMENT_LEARNING = "rl"
    PREFERENCE_OPTIMIZATION = "dpo"
    PREFERENCE_PAIRWISE = "ppo"


class DatasetFormat(str, Enum):
    """Dataset formats supported by LlamaFactory."""
    
    ALPACA = "alpaca"
    SHAREGPT = "sharegpt"
    CUSTOM = "custom"


@dataclass
class LlamaFactoryConfig:
    """Base configuration for LlamaFactory trainers."""
    
    model_path: str
    output_dir: str = field(default_factory=lambda: os.path.join(os.getcwd(), "outputs"))
    
    # Training parameters
    batch_size: int = 8
    num_epochs: int = 3
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    lr_scheduler_type: str = "cosine"
    warmup_ratio: float = 0.1
    
    # Model parameters
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    use_lora: bool = True
    
    # Data processing
    max_length: int = 1024
    dataset_format: DatasetFormat = DatasetFormat.ALPACA
    
    # Logging
    log_with: str = "mlflow"
    logging_steps: int = 10
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary for LlamaFactory CLI."""
        return {k: v.value if isinstance(v, Enum) else v 
                for k, v in self.__dict__.items()}


@dataclass
class SFTConfig(LlamaFactoryConfig):
    """Configuration for supervised fine-tuning."""
    
    strategy: TrainingStrategy = TrainingStrategy.SUPERVISED_FINETUNING
    train_file: str = ""
    val_file: Optional[str] = None
    
    # SFT specific settings
    cutoff_len: int = 1024
    normalize_data: bool = True
    

@dataclass
class RLConfig(LlamaFactoryConfig):
    """Configuration for reinforcement learning."""
    
    strategy: TrainingStrategy = TrainingStrategy.REINFORCEMENT_LEARNING
    reward_model: str = ""
    train_file: str = ""
    
    # RL specific settings
    kl_coef: float = 0.1
    top_k: int = 0
    top_p: float = 1.0
    temperature: float = 1.0
    

@dataclass
class DPOConfig(LlamaFactoryConfig):
    """Configuration for direct preference optimization."""
    
    strategy: TrainingStrategy = TrainingStrategy.PREFERENCE_OPTIMIZATION
    train_file: str = ""
    val_file: Optional[str] = None
    
    # DPO specific settings
    beta: float = 0.1
    reference_model: Optional[str] = None
    

def create_default_config(strategy: TrainingStrategy, model_path: str) -> LlamaFactoryConfig:
    """Create a default configuration based on the training strategy."""
    
    if strategy == TrainingStrategy.SUPERVISED_FINETUNING:
        return SFTConfig(model_path=model_path)
    elif strategy == TrainingStrategy.REINFORCEMENT_LEARNING:
        return RLConfig(model_path=model_path)
    elif strategy == TrainingStrategy.PREFERENCE_OPTIMIZATION:
        return DPOConfig(model_path=model_path)
    else:
        raise ValueError(f"Unsupported strategy: {strategy}") 
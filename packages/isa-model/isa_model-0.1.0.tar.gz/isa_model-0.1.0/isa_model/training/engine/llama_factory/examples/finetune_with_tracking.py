"""
Example of fine-tuning with LlamaFactory and MLflow tracking.

This example demonstrates how to use LlamaFactory for fine-tuning
and the MLflow tracking system to monitor and log the process.
"""

import os
import argparse
import logging
from typing import Dict, Any

from app.services.ai.models.training.engine.llama_factory import (
    LlamaFactory,
    DatasetFormat,
    TrainingStrategy
)
from app.services.ai.models.mlops import (
    TrainingTracker,
    ModelStage
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fine-tune with LlamaFactory and MLflow tracking")
    
    parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="Path or name of the base model"
    )
    parser.add_argument(
        "--train_data",
        type=str,
        required=True,
        help="Path to the training data"
    )
    parser.add_argument(
        "--val_data",
        type=str,
        help="Path to the validation data"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="outputs",
        help="Directory to save outputs"
    )
    parser.add_argument(
        "--dataset_format",
        type=str,
        choices=["alpaca", "sharegpt", "custom"],
        default="alpaca",
        help="Format of the dataset"
    )
    parser.add_argument(
        "--use_lora",
        action="store_true",
        help="Whether to use LoRA for training"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=8,
        help="Training batch size"
    )
    parser.add_argument(
        "--num_epochs",
        type=int,
        default=3,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=2e-5,
        help="Learning rate"
    )
    parser.add_argument(
        "--max_length",
        type=int,
        default=1024,
        help="Maximum sequence length"
    )
    parser.add_argument(
        "--lora_rank",
        type=int,
        default=8,
        help="LoRA rank parameter"
    )
    parser.add_argument(
        "--tracking_uri",
        type=str,
        help="URI for MLflow tracking server"
    )
    parser.add_argument(
        "--register_model",
        action="store_true",
        help="Whether to register the model in the registry"
    )
    
    return parser.parse_args()


def main():
    """Run the fine-tuning process with tracking."""
    args = parse_args()
    
    # Map dataset format string to enum
    dataset_format_map = {
        "alpaca": DatasetFormat.ALPACA,
        "sharegpt": DatasetFormat.SHAREGPT,
        "custom": DatasetFormat.CUSTOM
    }
    dataset_format = dataset_format_map[args.dataset_format]
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize LlamaFactory
    factory = LlamaFactory(base_output_dir=args.output_dir)
    
    # Initialize training tracker
    tracker = TrainingTracker(tracking_uri=args.tracking_uri)
    
    # Get model name from path
    model_name = os.path.basename(args.model_path)
    
    # Set up training parameters
    train_params = {
        "model_path": args.model_path,
        "train_data": args.train_data,
        "val_data": args.val_data,
        "output_dir": None,  # Will be set by factory
        "dataset_format": dataset_format,
        "use_lora": args.use_lora,
        "batch_size": args.batch_size,
        "num_epochs": args.num_epochs,
        "learning_rate": args.learning_rate,
        "max_length": args.max_length,
        "lora_rank": args.lora_rank
    }
    
    # Track the training run with MLflow
    with tracker.track_training_run(
        model_name=model_name,
        training_params=train_params,
        description=f"Fine-tuning {model_name} with LlamaFactory"
    ) as run_info:
        # Run the fine-tuning
        try:
            model_path = factory.finetune(**train_params)
            
            # Log success
            tracker.log_metrics({"success": 1.0})
            logger.info(f"Fine-tuning completed successfully. Model saved to {model_path}")
            
            # Register the model if requested
            if args.register_model:
                version = tracker.register_trained_model(
                    model_path=model_path,
                    description=f"Fine-tuned {model_name}",
                    stage=ModelStage.STAGING
                )
                logger.info(f"Model registered as version {version}")
                
        except Exception as e:
            # Log failure
            tracker.log_metrics({"success": 0.0})
            logger.error(f"Fine-tuning failed: {e}")
            raise


if __name__ == "__main__":
    main() 
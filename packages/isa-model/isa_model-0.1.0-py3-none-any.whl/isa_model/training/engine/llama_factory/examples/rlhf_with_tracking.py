"""
Example of RLHF (Reinforcement Learning from Human Feedback) with LlamaFactory and MLflow tracking.

This example demonstrates how to use LlamaFactory for RLHF
and the MLflow tracking system to monitor and log the process.
"""

import os
import argparse
import logging
from typing import Dict, Any

from app.services.ai.models.training.engine.llama_factory import (
    LlamaFactory,
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
    parser = argparse.ArgumentParser(description="Run RLHF with LlamaFactory and MLflow tracking")
    
    parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="Path or name of the base model"
    )
    parser.add_argument(
        "--reward_model",
        type=str,
        required=True,
        help="Path to the reward model"
    )
    parser.add_argument(
        "--train_data",
        type=str,
        required=True,
        help="Path to the training data"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="outputs",
        help="Directory to save outputs"
    )
    parser.add_argument(
        "--use_lora",
        action="store_true",
        help="Whether to use LoRA for training"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4,
        help="Training batch size"
    )
    parser.add_argument(
        "--num_epochs",
        type=int,
        default=1,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=1e-5,
        help="Learning rate"
    )
    parser.add_argument(
        "--kl_coef",
        type=float,
        default=0.1,
        help="KL coefficient for PPO"
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
    """Run the RLHF process with tracking."""
    args = parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize LlamaFactory
    factory = LlamaFactory(base_output_dir=args.output_dir)
    
    # Initialize training tracker
    tracker = TrainingTracker(tracking_uri=args.tracking_uri)
    
    # Get model name from path
    model_name = os.path.basename(args.model_path)
    
    # Set up RLHF parameters
    rl_params = {
        "model_path": args.model_path,
        "reward_model": args.reward_model,
        "train_data": args.train_data,
        "output_dir": None,  # Will be set by factory
        "use_lora": args.use_lora,
        "batch_size": args.batch_size,
        "num_epochs": args.num_epochs,
        "learning_rate": args.learning_rate,
        "kl_coef": args.kl_coef
    }
    
    # Track the RLHF run with MLflow
    with tracker.track_training_run(
        model_name=model_name,
        training_params=rl_params,
        description=f"RLHF for {model_name} with LlamaFactory",
        experiment_type="rl"
    ) as run_info:
        # Run the RLHF
        try:
            model_path = factory.rlhf(**rl_params)
            
            # Log success
            tracker.log_metrics({"success": 1.0})
            logger.info(f"RLHF completed successfully. Model saved to {model_path}")
            
            # Register the model if requested
            if args.register_model:
                version = tracker.register_trained_model(
                    model_path=model_path,
                    description=f"RLHF-tuned {model_name}",
                    stage=ModelStage.STAGING
                )
                logger.info(f"Model registered as version {version}")
                
        except Exception as e:
            # Log failure
            tracker.log_metrics({"success": 0.0})
            logger.error(f"RLHF failed: {e}")
            raise


if __name__ == "__main__":
    main() 
import json
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parents[4]  # Go up 4 levels from configs folder

flux_config = {
    "pretrained_model_name_or_path": "/home/Ubuntu/Downloads/flux1-dev.safetensors",
    # Update train_data_dir to your processed images
    "train_data_dir": str(project_root / "app/services/training/image_model/raw_data/training_images_processed"),
    "output_dir": "/home/Ubuntu/apps/StableSwarmUI/Models/diffusion_models",
    "output_name": "demi_flux_v1",
    "save_model_as": "safetensors",
    "learning_rate": 4e-6,
    "train_batch_size": 1,
    "epoch": 200,
    "save_every_n_epochs": 25,
    "mixed_precision": "bf16",
    "num_cpu_threads_per_process": 2,
    "flux1_t5xxl": "/home/Ubuntu/Downloads/t5xxl_fp16.safetensors",
    "flux1_clip_l": "/home/Ubuntu/Downloads/clip_l.safetensors",
}

config_path = Path(__file__).parent / "flux_config.json"
with open(config_path, "w") as f:
    json.dump(flux_config, f, indent=2) 
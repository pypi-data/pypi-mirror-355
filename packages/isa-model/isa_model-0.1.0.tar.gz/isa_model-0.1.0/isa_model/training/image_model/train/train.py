import json
import subprocess
from pathlib import Path

def train_lora():
    # Load your config
    with open('training_config.json', 'r') as f:
        config = json.load(f)
    
    # Construct the training command
    cmd = [
        "accelerate", "launch",
        "--num_cpu_threads_per_process", str(config["num_cpu_threads_per_process"]),
        "train_network.py",
        "--pretrained_model_name_or_path", config["pretrained_model_name_or_path"],
        "--train_data_dir", config["train_data_dir"],
        "--output_dir", config["output_dir"],
        "--output_name", config["output_name"],
        "--save_model_as", config["save_model_as"],
        "--learning_rate", str(config["learning_rate"]),
        "--train_batch_size", str(config["train_batch_size"]),
        "--epoch", str(config["epoch"]),
        "--save_every_n_epochs", str(config["save_every_n_epochs"]),
        "--mixed_precision", config["mixed_precision"],
        "--cache_latents",
        "--gradient_checkpointing"
    ]

    # Add FLUX specific parameters
    if config.get("flux1_checkbox"):
        cmd.extend([
            "--flux1_t5xxl", config["flux1_t5xxl"],
            "--flux1_clip_l", config["flux1_clip_l"],
            "--flux1_cache_text_encoder_outputs",
            "--flux1_cache_text_encoder_outputs_to_disk"
        ])

    # Execute the training
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    train_lora() 
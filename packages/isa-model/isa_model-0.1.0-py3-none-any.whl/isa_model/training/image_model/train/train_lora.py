import json
import subprocess
from pathlib import Path

def train_lora():
    # Load your config
    with open('training_config.json', 'r') as f:
        config = json.load(f)
    
    # Construct the training command for LoRA
    cmd = [
        "accelerate", "launch",
        "--num_cpu_threads_per_process", str(config["num_cpu_threads_per_process"]),
        "sdxl_train_network.py",  # Use the SDXL LoRA training script
        "--network_module", "networks.lora",  # Specify LoRA network
        "--pretrained_model_name_or_path", config["pretrained_model_name_or_path"],
        "--train_data_dir", config["train_data_dir"],
        "--output_dir", config["output_dir"],
        "--output_name", config["output_name"],
        "--save_model_as", config["save_model_as"],
        "--network_alpha", "1",  # LoRA alpha parameter
        "--network_dim", "32",   # LoRA dimension
        "--learning_rate", str(config["learning_rate"]),
        "--train_batch_size", str(config["train_batch_size"]),
        "--max_train_epochs", str(config["epoch"]),
        "--save_every_n_epochs", str(config["save_every_n_epochs"]),
        "--mixed_precision", config["mixed_precision"],
        "--cache_latents",
        "--gradient_checkpointing",
        "--network_args", "conv_dim=32", "conv_alpha=1",  # LoRA network arguments
        "--noise_offset", "0.1",
        "--adaptive_noise_scale", "0.01",
        "--max_resolution", "1024,1024",
        "--min_bucket_reso", "256",
        "--max_bucket_reso", "1024",
        "--xformers",
        "--bucket_reso_steps", "64",
        "--caption_extension", ".txt",
        "--optimizer_type", "AdaFactor",
        "--optimizer_args", "scale_parameter=False", "relative_step=False", "warmup_init=False",
        "--lr_scheduler", "constant"
    ]

    # Add FLUX specific parameters for LoRA
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
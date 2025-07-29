import json
import subprocess
from pathlib import Path

def train_flux():
    # Load your config
    with open('flux_config.json', 'r') as f:
        config = json.load(f)
    
    # Construct the training command for Flux finetuning
    cmd = [
        "accelerate", "launch",
        "--num_cpu_threads_per_process", str(config["num_cpu_threads_per_process"]),
        "train_db.py",
        "--pretrained_model_name_or_path", config["pretrained_model_name_or_path"],
        "--train_data_dir", config["train_data_dir"],
        "--output_dir", config["output_dir"],
        "--output_name", config["output_name"],
        "--train_batch_size", str(config["train_batch_size"]),
        "--save_every_n_epochs", str(config["save_every_n_epochs"]),
        "--learning_rate", str(config["learning_rate"]),
        "--max_train_epochs", str(config["epoch"]),
        "--mixed_precision", config["mixed_precision"],
        "--save_model_as", config["save_model_as"],
        "--cache_latents",
        "--cache_latents_to_disk",
        "--gradient_checkpointing",
        "--optimizer_type", "Adafactor",
        "--optimizer_args", "scale_parameter=False relative_step=False warmup_init=False weight_decay=0.01",
        "--max_resolution", "1024,1024",
        "--full_bf16",
        "--flux1_checkbox",
        "--flux1_t5xxl", config["flux1_t5xxl"],
        "--flux1_clip_l", config["flux1_clip_l"],
        "--flux1_cache_text_encoder_outputs",
        "--flux1_cache_text_encoder_outputs_to_disk",
        "--flux_fused_backward_pass"
    ]

    # Execute the training
    subprocess.run(cmd, check=True) 
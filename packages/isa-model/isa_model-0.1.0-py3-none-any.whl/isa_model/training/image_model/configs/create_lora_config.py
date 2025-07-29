import json

lora_config = {
    "pretrained_model_name_or_path": "/home/Ubuntu/Downloads/flux1-dev.safetensors",
    "train_data_dir": "/home/Ubuntu/Downloads/training_imgs",
    "output_dir": "/home/Ubuntu/apps/StableSwarmUI/Models/lora",
    "output_name": "demi_lora_v1",
    "save_model_as": "safetensors",
    "learning_rate": 1e-4,
    "train_batch_size": 1,
    "epoch": 100,
    "save_every_n_epochs": 10,
    "mixed_precision": "bf16",
    "num_cpu_threads_per_process": 2,
    "flux1_checkbox": True,
    "flux1_t5xxl": "/home/Ubuntu/Downloads/t5xxl_fp16.safetensors",
    "flux1_clip_l": "/home/Ubuntu/Downloads/clip_l.safetensors",
}

with open("lora_config.json", "w") as f:
    json.dump(lora_config, f, indent=2) 
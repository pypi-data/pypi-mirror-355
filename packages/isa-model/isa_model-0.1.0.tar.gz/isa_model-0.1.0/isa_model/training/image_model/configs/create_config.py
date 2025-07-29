import json

config = {
    "general": {
        "enable_bucket": True,
        "min_bucket_reso": 256,
        "max_bucket_reso": 1024,
        "batch_size_per_device": 4,
        "train_batch_size": 4,
        "epoch": 100,
        "save_every_n_epochs": 10,
        "save_model_as": "safetensors",
        "mixed_precision": "fp16",
        "seed": 42,
        "num_cpu_threads_per_process": 8
    },
    "model": {
        "pretrained_model_name_or_path": "runwayml/stable-diffusion-v1-5",
        "v2": False,
        "v_parameterization": False
    },
    "optimizer": {
        "learning_rate": 1e-5,
        "lr_scheduler": "cosine_with_restarts",
        "lr_warmup_steps": 100,
        "optimizer_type": "AdamW8bit"
    },
    "dataset": {
        "resolution": 512,
        "center_crop": False,
        "random_crop": False,
        "flip_aug": True
    }
}

with open("training_config.json", "w") as f:
    json.dump(config, f, indent=2) 
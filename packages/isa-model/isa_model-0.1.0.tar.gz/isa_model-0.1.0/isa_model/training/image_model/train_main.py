import os
from pathlib import Path
import shutil
from app.services.training.image_model.raw_data.create_lora_captions import create_lora_captions
from app.services.training.image_model.train.train_flux import train_flux

def main():
    # Setup paths
    project_root = Path(__file__).parent
    processed_images_dir = project_root / "raw_data/training_images_processed"
    
    # 1. Generate captions for all processed images
    print("Creating captions for processed images...")
    create_lora_captions(processed_images_dir)
    
    # 2. Create Flux config
    print("Creating Flux configuration...")
    os.system(f"python {project_root}/configs/create_flux_config.py")
    
    # 3. Run Flux training
    print("Starting Flux training...")
    train_flux()

if __name__ == "__main__":
    main() 
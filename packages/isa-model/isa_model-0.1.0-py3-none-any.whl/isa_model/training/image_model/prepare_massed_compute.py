import os
import shutil
from pathlib import Path

def prepare_massed_package():
    # Get current directory and create desktop folder structure
    project_root = Path(__file__).parent
    desktop_dir = Path.home() / "Desktop" / "massed_training"
    
    # Create necessary directories
    desktop_dir.mkdir(parents=True, exist_ok=True)
    training_dir = desktop_dir / "training_imgs"
    training_dir.mkdir(exist_ok=True)
    
    # Copy processed images and captions
    processed_images_dir = project_root / "raw_data/training_images_processed"
    for img_file in processed_images_dir.glob("*.jpg"):
        shutil.copy2(img_file, training_dir)
        # Copy or create corresponding caption file
        caption_file = img_file.with_suffix(".txt")
        if caption_file.exists():
            shutil.copy2(caption_file, training_dir)
        else:
            with open(training_dir / f"{img_file.stem}.txt", "w") as f:
                f.write("a photo of demi person, (high quality, photorealistic:1.2), professional portrait")
    
    # Create Kohya FLUX setup script
    kohya_script = """#!/bin/bash
cd /home/Ubuntu/apps/kohya_ss

git pull

git checkout sd3-flux.1

source venv/bin/activate

./setup.sh

git submodule update --init --recursive

pip uninstall xformers --yes

pip install torch==2.5.1+cu124 torchvision --index-url https://download.pytorch.org/whl/cu124

pip install xformers==0.0.28.post3 --index-url https://download.pytorch.org/whl/cu124

./gui.sh --listen=0.0.0.0 --inbrowser --noverify

# Keep the terminal open
read -p "Press Enter to continue..."
"""
    
    # Create Models download script
    models_script = """#!/bin/bash
pip install huggingface_hub

pip install ipywidgets
pip install hf_transfer
export HF_HUB_ENABLE_HF_TRANSFER=1

python3 Download_Train_Models.py --dir /home/Ubuntu/Downloads
"""
    
    # Write scripts
    with open(desktop_dir / "Massed_Compute_Kohya_FLUX.sh", "w", newline='\n') as f:
        f.write(kohya_script)
    
    with open(desktop_dir / "Massed_Compute_Download_Models.sh", "w", newline='\n') as f:
        f.write(models_script)
    
    # Make scripts executable
    os.chmod(desktop_dir / "Massed_Compute_Kohya_FLUX.sh", 0o755)
    os.chmod(desktop_dir / "Massed_Compute_Download_Models.sh", 0o755)
    
    print(f"""
Package prepared in: {desktop_dir}

Next steps:
1. Upload the entire '{desktop_dir.name}' folder to your Massed Compute instance
2. In Massed Compute terminal:
   cd ~/Desktop/massed_training
   chmod +x Massed_Compute_Kohya_FLUX.sh
   ./Massed_Compute_Kohya_FLUX.sh

3. In a new terminal:
   cd ~/Desktop/massed_training
   chmod +x Massed_Compute_Download_Models.sh
   ./Massed_Compute_Download_Models.sh

4. When Kohya GUI opens (http://0.0.0.0:7860/):
   - Go to the Training tab
   - Set training data directory to: /home/Ubuntu/Desktop/massed_training/training_imgs
   - Use the settings from the Flux tutorial
    """)

if __name__ == "__main__":
    prepare_massed_package() 
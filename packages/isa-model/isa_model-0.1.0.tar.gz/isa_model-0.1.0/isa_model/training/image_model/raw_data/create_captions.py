import os
from pathlib import Path

def create_captions(image_dir):
    """Create a caption file for each image with a basic description"""
    image_dir = Path(image_dir)
    
    for image_file in image_dir.glob("*.jpg"):
        caption_file = image_dir / f"{image_file.stem}.txt"
        
        # Create a basic caption - you can modify this
        with open(caption_file, "w") as f:
            f.write("a photo of demi")

# Use the function
create_captions("training_data/demi") 
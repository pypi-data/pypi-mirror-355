from pathlib import Path

def create_lora_captions(image_dir):
    """Create detailed captions for LoRA training"""
    image_dir = Path(image_dir)
    
    # LoRA-specific caption with trigger word
    caption_text = (
        "a photo of demi person, (high quality, photorealistic:1.2), "
        "professional portrait, detailed facial features, "
        "natural lighting, sharp focus, clear skin texture"
    )
    
    for image_file in image_dir.glob("*.jpg"):
        caption_file = image_dir / f"{image_file.stem}.txt"
        with open(caption_file, "w") as f:
            f.write(caption_text)

# Use the function
create_lora_captions("/home/Ubuntu/Downloads/training_imgs") 
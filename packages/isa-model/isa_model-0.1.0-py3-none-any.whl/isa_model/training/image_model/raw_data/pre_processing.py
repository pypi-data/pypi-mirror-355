import os
import cv2
import logging
from PIL import Image
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import shutil
from ultralytics import YOLO
import numpy
from pillow_heif import register_heif_opener

# Configure logging and PIL settings
logging.basicConfig(level=logging.INFO)
Image.MAX_IMAGE_PIXELS = None
register_heif_opener()  # This enables HEIC support in PIL

COCO_CLASSES = {
    'person': 0, 'bicycle': 1, 'car': 2, 'motorcycle': 3, 'airplane': 4, 'bus': 5, 'train': 6,
    'truck': 7, 'boat': 8, 'traffic light': 9, 'fire hydrant': 10, 'stop sign': 11,
    'parking meter': 12, 'bench': 13, 'bird': 14, 'cat': 15, 'dog': 16, 'horse': 17,
    'sheep': 18, 'cow': 19, 'elephant': 20, 'bear': 21, 'zebra': 22, 'giraffe': 23,
    'backpack': 24, 'umbrella': 25, 'handbag': 26, 'tie': 27, 'suitcase': 28, 'frisbee': 29,
    'skis': 30, 'snowboard': 31, 'sports ball': 32, 'kite': 33, 'baseball bat': 34,
    'baseball glove': 35, 'skateboard': 36, 'surfboard': 37, 'tennis racket': 38,
    'bottle': 39, 'wine glass': 40, 'cup': 41, 'fork': 42, 'knife': 43, 'spoon': 44,
    'bowl': 45, 'banana': 46, 'apple': 47, 'sandwich': 48, 'orange': 49, 'broccoli': 50,
    'carrot': 51, 'hot dog': 52, 'pizza': 53, 'donut': 54, 'cake': 55, 'chair': 56,
    'couch': 57, 'potted plant': 58, 'bed': 59, 'dining table': 60, 'toilet': 61,
    'tv': 62, 'laptop': 63, 'mouse': 64, 'remote': 65, 'keyboard': 66, 'cell phone': 67,
    'microwave': 68, 'oven': 69, 'toaster': 70, 'sink': 71, 'refrigerator': 72,
    'book': 73, 'clock': 74, 'vase': 75, 'scissors': 76, 'teddy bear': 77,
    'hair drier': 78, 'toothbrush': 79
}

class ImagePreProcessor:
    def __init__(self, input_dir: str, output_dir: str, target_size: tuple = (512, 512), 
                 padding: float = 0.3):
        """
        Initialize the image preprocessor
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.target_size = target_size
        self.padding = padding
        self.supported_formats = {'.jpg', '.jpeg', '.heic', '.png'}
        
        # Load YOLO face detection model
        try:
            logging.info("Loading YOLO face detection model...")
            current_dir = Path(__file__).parent  # Get the directory where this script is located
            model_path = current_dir / "models" / "yolov8n-face.pt"
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}")
            self.model = YOLO(str(model_path))  # Convert Path to string for YOLO
            logging.info("Successfully loaded YOLO face detection model")
        except Exception as e:
            logging.error(f"Failed to load YOLO model: {str(e)}")
            raise

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def detect_and_crop_face(self, img) -> tuple:
        """
        Detect face in image and return cropped region
        """
        cv2_img = cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2BGR)
        results = self.model(cv2_img)
        
        # Get all face detections
        detections = results[0].boxes
        
        if len(detections) == 0:
            return False, None
            
        # Get coordinates of the first detected face
        box = detections[0]
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        
        # Add padding
        width = x2 - x1
        height = y2 - y1
        padding_x = int(width * self.padding)
        padding_y = int(height * self.padding)
        
        x1 = max(0, x1 - padding_x)
        y1 = max(0, y1 - padding_y)
        x2 = min(img.width, x2 + padding_x)
        y2 = min(img.height, y2 + padding_y)
        
        cropped_img = img.crop((x1, y1, x2, y2))
        return True, cropped_img

    def process_image(self, image_path: Path) -> tuple:
        """
        Process a single image
        
        Args:
            image_path (Path): Path to input image
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Handle HEIC/HEIF files
            if image_path.suffix.lower() in {'.heic', '.heif'}:
                try:
                    with Image.open(image_path) as img:
                        # Convert HEIC to RGB mode
                        img = img.convert('RGB')
                        detected, cropped_img = self.detect_and_crop_face(img)
                        if not detected:
                            return False, f"No face detected in {image_path.name}"
                except Exception as e:
                    return False, f"Error processing HEIC file {image_path.name}: {str(e)}"
            else:
                # Handle other image formats
                with Image.open(image_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    detected, cropped_img = self.detect_and_crop_face(img)
                    if not detected:
                        return False, f"No face detected in {image_path.name}"
            
            # Process the cropped image
            aspect_ratio = cropped_img.width / cropped_img.height
            if aspect_ratio > 1:
                new_width = self.target_size[0]
                new_height = int(self.target_size[0] / aspect_ratio)
            else:
                new_height = self.target_size[1]
                new_width = int(self.target_size[1] * aspect_ratio)

            cropped_img = cropped_img.resize((new_width, new_height), Image.LANCZOS)
            
            new_img = Image.new('RGB', self.target_size, (0, 0, 0))
            paste_x = (self.target_size[0] - new_width) // 2
            paste_y = (self.target_size[1] - new_height) // 2
            new_img.paste(cropped_img, (paste_x, paste_y))
            
            output_path = self.output_dir / f"{image_path.stem}.jpg"
            new_img.save(output_path, 'JPEG', quality=95)
            
            return True, f"Successfully processed {image_path.name}"

        except Exception as e:
            return False, f"Error processing {image_path.name}: {str(e)}"

    def process_directory(self, num_workers: int = 4):
        """
        Process all images in the input directory
        
        Args:
            num_workers (int): Number of worker processes to use
        """
        # Get list of all images
        image_files = [
            f for f in self.input_dir.iterdir() 
            if f.is_file() and f.suffix.lower() in self.supported_formats
        ]
        
        if not image_files:
            logging.warning("No supported image files found in input directory")
            return

        logging.info(f"Found {len(image_files)} images to process")
        
        # Process images using multiple workers
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            with tqdm(total=len(image_files), desc="Processing images") as pbar:
                futures = []
                for image_path in image_files:
                    future = executor.submit(self.process_image, image_path)
                    future.add_done_callback(lambda p: pbar.update(1))
                    futures.append(future)
                
                # Process results
                for future in futures:
                    success, message = future.result()
                    if not success:
                        logging.error(message)

def main():
    # Update paths to use project-relative directories
    current_dir = Path(__file__).parent  # Get the directory where this script is located
    input_dir = current_dir / "data" / "training_images"
    output_dir = current_dir / "data" / "training_images_processed"
    
    processor = ImagePreProcessor(
        input_dir=input_dir,
        output_dir=output_dir,
        target_size=(512, 512),  # Good size for Kohya training
        padding=0.3,             # 30% padding around faces
    )
    
    processor.process_directory(num_workers=4)

if __name__ == "__main__":
    main()

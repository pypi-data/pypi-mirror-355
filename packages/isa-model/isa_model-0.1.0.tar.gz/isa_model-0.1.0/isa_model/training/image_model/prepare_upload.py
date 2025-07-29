import shutil
import os

def prepare_training_package():
    # Create a directory for all training materials
    os.makedirs("training_package", exist_ok=True)
    
    # Copy training data
    shutil.copytree("training_data", "training_package/training_data", dirs_exist_ok=True)
    
    # Copy config
    shutil.copy("training_config.json", "training_package/training_config.json")
    
    # Create zip file
    shutil.make_archive("demi_training", "zip", "training_package")

prepare_training_package() 
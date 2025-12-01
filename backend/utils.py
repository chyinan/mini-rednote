import os
import uuid

IMAGE_DIR = "assets"

def save_image(uploaded_file):
    """Save uploaded image to assets directory and return the path."""
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
    
    file_ext = os.path.splitext(uploaded_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(IMAGE_DIR, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.file.read())
        
    return file_path


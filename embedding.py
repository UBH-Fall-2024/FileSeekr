import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import os
import numpy as np
from pathlib import Path

# Load the CLIP model and processor
model_name = "laion/CLIP-ViT-H-14-laion2B-s32B-b79K"
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained(model_name)
processor = CLIPProcessor.from_pretrained(model_name)
model.to(device)
model.eval()

def get_image_embedding(file_path: str):
    """
    Generate and return the embedding for an image file using CLIP.
    
    Args:
        file_path (str): Path to the image file
    Returns:
        numpy.ndarray: The image embedding
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        image = Image.open(file_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.get_image_features(**inputs)
        
        embeddings = outputs.cpu().numpy()
        embeddings = embeddings / np.linalg.norm(embeddings, axis=-1, keepdims=True)
        
        return embeddings[0]
    
    except Exception as e:
        raise ValueError(f"Error processing image {file_path}: {e}")

def get_text_embedding(text_content: str):
    """
    Generate and return the embedding for text content using CLIP.
    
    Args:
        text_content (str): The text to embed
    Returns:
        numpy.ndarray: The text embedding
    """
    try:
        inputs = processor(text=text_content, return_tensors="pt", padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.get_text_features(**inputs)
        
        embeddings = outputs.cpu().numpy()
        embeddings = embeddings / np.linalg.norm(embeddings, axis=-1, keepdims=True)
        
        return embeddings[0]
    
    except Exception as e:
        raise ValueError(f"Error processing text: {e}")

def get_embedding(file_path: str):
    """
    Generate embedding based on file type.
    
    Args:
        file_path (str): Path to the file
    Returns:
        numpy.ndarray: The embedding
    """
    file_path = Path(file_path)
    
    # Image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    # Text extensions
    text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json'}
    
    if file_path.suffix.lower() in image_extensions:
        return get_image_embedding(str(file_path))
    elif file_path.suffix.lower() in text_extensions:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
                return get_text_embedding(content)
            except UnicodeDecodeError:
                raise ValueError(f"Unable to read text file: {file_path}")
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import os
import numpy as np

# Load the CLIP model and processor
model_name = "laion/CLIP-ViT-H-14-laion2B-s32B-b79K"
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained(model_name)
processor = CLIPProcessor.from_pretrained(model_name)
model.to(device)
model.eval()

def get_embedding(file_path: str):
    """
    Generate and return the embedding for the given image file using CLIP.
    
    Args:
        file_path (str): Path to the image file for which to generate the embedding.
    
    Returns:
        embedding (numpy.ndarray): The generated embedding vector.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        # Open the image file
        image = Image.open(file_path).convert("RGB")
    except Exception as e:
        raise ValueError(f"Error opening image file {file_path}: {e}")
    
    # Preprocess the image
    inputs = processor(images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        # Get image embeddings
        outputs = model.get_image_features(**inputs)
    
    # Normalize the embeddings
    embeddings = outputs.cpu().numpy()
    embeddings = embeddings / np.linalg.norm(embeddings, axis=-1, keepdims=True)
    
    return embeddings[0] 
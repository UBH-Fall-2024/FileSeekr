from pathlib import Path
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from typing import List, Optional, Dict
import fitz, io, numpy as np, openvino as ov, os, torch

# Load the CLIP model and processor
model_name = "laion/CLIP-ViT-H-14-laion2B-s32B-b79K"
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained(model_name)
processor = CLIPProcessor.from_pretrained(model_name)

# Initialize OpenVINO
core = ov.Core()
try:
    # Load optimized models if they exist, otherwise create them
    if os.path.exists("optimized_image_model.xml") and os.path.exists("optimized_text_model.xml"):
        image_model = core.compile_model("optimized_image_model.xml")
        text_model = core.compile_model("optimized_text_model.xml")
    else:
        image_model, text_model = optimize_clip_model()
    
    USE_OPTIMIZED = True
except Exception as e:
    print(f"Failed to load optimized models: {e}. Falling back to PyTorch models.")
    model.to(device)
    model.eval()
    USE_OPTIMIZED = False

class ImageFeatureExtractor(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.vision_model = model.vision_model
        
    def forward(self, pixel_values):
        return self.vision_model(pixel_values)[1]

class TextFeatureExtractor(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.text_model = model.text_model
        
    def forward(self, input_ids, attention_mask):
        return self.text_model(input_ids=input_ids, attention_mask=attention_mask)[1]

def optimize_clip_model():
    """Create and save optimized OpenVINO models for both image and text processing"""
    # Initialize OpenVINO
    core = ov.Core()
    
    # Prepare example inputs
    example_image = torch.randn(1, 3, 224, 224)
    example_text = {
        'input_ids': torch.randint(0, 1000, (1, 77)),
        'attention_mask': torch.ones(1, 77)
    }
    
    # Convert image model
    image_model = ImageFeatureExtractor(model)
    ov_image_model = ov.convert_model(image_model, example_input=example_image)
    ov.save_model(ov_image_model, "optimized_image_model.xml")
    
    # Convert text model
    text_model = TextFeatureExtractor(model)
    ov_text_model = ov.convert_model(text_model, example_input=example_text)
    ov.save_model(ov_text_model, "optimized_text_model.xml")
    
    return (core.compile_model("optimized_image_model.xml"), 
            core.compile_model("optimized_text_model.xml"))

def get_image_embedding(file_path: str):
    """Generate and return the embedding for an image file using optimized CLIP"""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        image = Image.open(file_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        
        if USE_OPTIMIZED:
            # Use OpenVINO model
            image_tensor = inputs['pixel_values'].numpy()
            embeddings = image_model(image_tensor)[0]
        else:
            # Fallback to PyTorch model
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.no_grad():
                embeddings = model.get_image_features(**inputs).cpu().numpy()
        
        embeddings = embeddings / np.linalg.norm(embeddings, axis=-1, keepdims=True)
        return embeddings[0]
    
    except Exception as e:
        raise ValueError(f"Error processing image {file_path}: {e}")

def get_text_embedding(text_content: str):
    """Generate and return the embedding for text content using optimized CLIP"""
    try:
        inputs = processor(text=text_content, return_tensors="pt", padding=True)
        
        if USE_OPTIMIZED:
            # Use OpenVINO model
            text_inputs = {
                'input_ids': inputs['input_ids'].numpy(),
                'attention_mask': inputs['attention_mask'].numpy()
            }
            embeddings = text_model(text_inputs)[0]
        else:
            # Fallback to PyTorch model
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.no_grad():
                embeddings = model.get_text_features(**inputs).cpu().numpy()
        
        embeddings = embeddings / np.linalg.norm(embeddings, axis=-1, keepdims=True)
        return embeddings[0]
    
    except Exception as e:
        raise ValueError(f"Error processing text: {e}")

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        file_path (str): Path to the PDF file
    Returns:
        str: Extracted text content
    """
    try:
        doc = fitz.open(file_path)
        text_content = []
        
        for page in doc:
            text_content.append(page.get_text())
        
        return "\n".join(text_content)
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF {file_path}: {e}")

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
    # PDF extension
    pdf_extension = {'.pdf'}
    
    if file_path.suffix.lower() in image_extensions:
        return get_image_embedding(str(file_path))
    elif file_path.suffix.lower() in text_extensions:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
                return get_text_embedding(content)
            except UnicodeDecodeError:
                raise ValueError(f"Unable to read text file: {file_path}")
    elif file_path.suffix.lower() in pdf_extension:
        try:
            content = extract_text_from_pdf(str(file_path))
            # If PDF has no text content, try to process it as an image
            if not content.strip():
                print(f"No text found in PDF {file_path}, attempting to process first page as image...")
                doc = fitz.open(str(file_path))
                if doc.page_count > 0:
                    page = doc[0]
                    pix = page.get_pixmap()
                    img_data = pix.tobytes()
                    img = Image.frombytes("RGB", [pix.width, pix.height], img_data)
                    # Create a temporary buffer for the image
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    buffer.seek(0)
                    # Process as image
                    return get_image_embedding_from_buffer(buffer)
                else:
                    raise ValueError("PDF has no pages")
            return get_text_embedding(content)
        except Exception as e:
            raise ValueError(f"Error processing PDF {file_path}: {e}")
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

def get_image_embedding_from_buffer(buffer):
    """
    Generate embedding for an image from a buffer.
    
    Args:
        buffer (io.BytesIO): Buffer containing the image data
    Returns:
        numpy.ndarray: The image embedding
    """
    try:
        image = Image.open(buffer).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.get_image_features(**inputs)
        
        embeddings = outputs.cpu().numpy()
        embeddings = embeddings / np.linalg.norm(embeddings, axis=-1, keepdims=True)
        
        return embeddings[0]
    except Exception as e:
        raise ValueError(f"Error processing image from buffer: {e}")


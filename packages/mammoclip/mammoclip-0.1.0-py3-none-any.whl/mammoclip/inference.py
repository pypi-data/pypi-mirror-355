#!/usr/bin/env python3
"""
Mammo-CLIP Inference Module
Provides a clean API for using pretrained Mammo-CLIP models
"""

import os
import sys
import torch
import numpy as np
from typing import Dict, List, Union, Optional
from scipy.special import softmax
from transformers import AutoTokenizer

# Set Hugging Face cache directory to a writable location
cache_dir = os.path.expanduser("~/.cache/huggingface")
os.environ['HF_HOME'] = cache_dir
os.environ['TRANSFORMERS_CACHE'] = cache_dir
os.makedirs(cache_dir, exist_ok=True)

# Add codebase to Python path
codebase_path = os.path.join(os.path.dirname(__file__), '..', 'codebase')
if codebase_path not in sys.path:
    sys.path.insert(0, codebase_path)

# Import the standalone model loader to avoid dependency issues
try:
    from .model_loader import build_mammo_clip_model
    _build_model_available = True
except ImportError as e:
    print(f"Warning: Could not import standalone model loader: {e}")
    _build_model_available = False


class MammoClipModel:
    """
    Mammo-CLIP model for zero-shot mammography analysis
    """
    
    def __init__(self, checkpoint_path: Optional[str] = None, model_name: str = "efficientnet_b5", device: Optional[str] = None):
        """
        Initialize the Mammo-CLIP model
        
        Args:
            checkpoint_path: Path to the model checkpoint (.tar file). If None, will download from HuggingFace
            model_name: Name of the pretrained model to use (default: efficientnet_b5)
            device: Device to use ('cpu', 'cuda', or None for auto-detection)
        """
        self.device = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))
        print(f"Using device: {self.device}")
        
        # Get checkpoint path - either provided or download from HuggingFace
        if checkpoint_path is None:
            print(f"No checkpoint provided, downloading model: {model_name}")
            try:
                from .model_downloader import get_model_path
                checkpoint_path = get_model_path(model_name, auto_download=True)
            except ImportError:
                raise ImportError("Model downloader not available. Please provide checkpoint_path manually.")
        
        # Load checkpoint
        print(f"Loading checkpoint: {checkpoint_path}")
        # Handle PyTorch 2.6+ security change - use weights_only=False for trusted checkpoint
        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        self.ckpt_config = ckpt["config"]
        
        # Initialize tokenizer with explicit cache directory
        self.tokenizer = AutoTokenizer.from_pretrained(
            "emilyalsentzer/Bio_ClinicalBERT",
            cache_dir=cache_dir
        )
        
        # Build model using standalone loader
        if not _build_model_available:
            raise ImportError("Model loader not available. Cannot build model.")
            
        self.model = build_mammo_clip_model(
            model_config=self.ckpt_config["model"],
            loss_config=self.ckpt_config["loss"],
            tokenizer=self.tokenizer
        )
        
        # Load model weights
        self.model.load_state_dict(ckpt["model"], strict=False)
        self.model = self.model.to(self.device)
        self.model.eval()
        
        print("Model loaded successfully!")
    
    def encode_image(self, image: Union[torch.Tensor, np.ndarray, str]) -> np.ndarray:
        """
        Encode image(s) using CLIP image encoder
        
        Args:
            image: Image input - can be:
                - torch.Tensor: Preprocessed image tensor [B, C, H, W] or [C, H, W]
                - np.ndarray: Preprocessed image array
                - str: Path to DICOM file
        
        Returns:
            Normalized image embeddings as numpy array
        """
        from .utils import process_dicom_image, preprocess_image
        
        # Handle different input types
        if isinstance(image, str):
            # DICOM file path
            processed_img = process_dicom_image(image)
            image_tensor = preprocess_image(processed_img)
        elif isinstance(image, np.ndarray):
            # Numpy array - assume it's already processed
            image_tensor = preprocess_image(image)
        elif isinstance(image, torch.Tensor):
            # Tensor - assume it's already preprocessed
            image_tensor = image
            if len(image_tensor.shape) == 3:
                image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
        
        with torch.no_grad():
            img_emb = self.model.encode_image(image_tensor.to(self.device))
            img_emb = self.model.image_projection(img_emb) if self.model.projection else img_emb
            img_emb = img_emb / torch.norm(img_emb, dim=1, keepdim=True)
        
        return img_emb.detach().cpu().numpy()
    
    def encode_text(self, text_prompts: Union[str, List[str]]) -> np.ndarray:
        """
        Encode text prompt(s) using CLIP text encoder
        
        Args:
            text_prompts: Text prompt(s) - can be a single string or list of strings
        
        Returns:
            Normalized text embeddings as numpy array
        """
        if isinstance(text_prompts, str):
            text_prompts = [text_prompts]
        
        text_tokens = self.tokenizer(
            text_prompts, 
            padding="longest", 
            truncation=True, 
            return_tensors="pt",
            max_length=256
        )
        
        with torch.no_grad():
            text_emb = self.model.encode_text(text_tokens.to(self.device))
            text_emb = self.model.text_projection(text_emb) if self.model.projection else text_emb
            text_emb = text_emb / torch.norm(text_emb, dim=1, keepdim=True)
        
        return text_emb.detach().cpu().numpy()
    
    def predict(self, image: Union[torch.Tensor, np.ndarray, str], 
                prompts_dict: Dict[str, List[str]]) -> Dict:
        """
        Perform zero-shot inference on image with multiple categories
        
        Args:
            image: Image input (same as encode_image)
            prompts_dict: Dictionary of {category: [prompt1, prompt2, ...]}
        
        Returns:
            Dictionary with prediction results for each category
        """
        # Get image embedding
        image_embedding = self.encode_image(image)
        
        results = {}
        
        # For each category, compute similarity
        for category, prompts in prompts_dict.items():
            # Get text embeddings
            text_embeddings = self.encode_text(prompts)
            
            # Compute similarities and apply softmax
            similarities = softmax(
                np.dot(image_embedding, text_embeddings.T), axis=1
            )
            
            # Get probabilities for each prompt
            probabilities = similarities[0]
            
            results[category] = {
                'prompts': prompts,
                'probabilities': probabilities.tolist(),
                'prediction': prompts[np.argmax(probabilities)],
                'confidence': float(np.max(probabilities))
            }
        
        return results


# Module-level instances for convenience
_default_model = None
_default_checkpoint_path = None


def load_model(checkpoint_path: Optional[str] = None, model_name: str = "efficientnet_b5", device: Optional[str] = None) -> MammoClipModel:
    """
    Load a Mammo-CLIP model from checkpoint or download from HuggingFace
    
    Args:
        checkpoint_path: Path to model checkpoint (optional, will download if None)
        model_name: Name of the pretrained model to use (default: efficientnet_b5)
        device: Device to use ('cpu', 'cuda', or None for auto-detection)
    
    Returns:
        Loaded MammoClipModel instance
    """
    global _default_model, _default_checkpoint_path
    
    # Create a cache key that includes both checkpoint path and model name
    cache_key = f"{checkpoint_path}_{model_name}"
    
    # Cache the default model if it's the same configuration
    if _default_model is None or _default_checkpoint_path != cache_key:
        _default_model = MammoClipModel(checkpoint_path, model_name, device)
        _default_checkpoint_path = cache_key
    
    return _default_model


def encode_image(image: Union[torch.Tensor, np.ndarray, str], 
                 checkpoint_path: Optional[str] = None,
                 model_name: str = "efficientnet_b5",
                 model: Optional[MammoClipModel] = None) -> np.ndarray:
    """
    Encode image using default or provided model
    
    Args:
        image: Image input
        checkpoint_path: Path to checkpoint (optional, will download if None)
        model_name: Name of the pretrained model to use (default: efficientnet_b5)
        model: Pre-loaded MammoClipModel instance
    
    Returns:
        Image embeddings
    """
    if model is None:
        model = load_model(checkpoint_path, model_name)
    
    return model.encode_image(image)


def encode_text(text_prompts: Union[str, List[str]], 
                checkpoint_path: Optional[str] = None,
                model_name: str = "efficientnet_b5",
                model: Optional[MammoClipModel] = None) -> np.ndarray:
    """
    Encode text using default or provided model
    
    Args:
        text_prompts: Text prompt(s)
        checkpoint_path: Path to checkpoint (optional, will download if None)
        model_name: Name of the pretrained model to use (default: efficientnet_b5)
        model: Pre-loaded MammoClipModel instance
    
    Returns:
        Text embeddings
    """
    if model is None:
        model = load_model(checkpoint_path, model_name)
    
    return model.encode_text(text_prompts) 
"""
Mammo-CLIP: A pretrained CLIP model for mammography analysis
"""

from .inference import MammoClipModel, encode_image, encode_text, load_model
from .utils import process_dicom_image, preprocess_image
from .model_downloader import download_model, list_available_models

__version__ = "0.1.0"
__all__ = [
    "MammoClipModel", 
    "load_model",
    "encode_image", 
    "encode_text", 
    "process_dicom_image", 
    "preprocess_image",
    "download_model",
    "list_available_models"
] 
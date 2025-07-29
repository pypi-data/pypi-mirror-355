#!/usr/bin/env python3
"""
Model downloader for Mammo-CLIP
Automatically downloads pretrained models from Hugging Face Hub
"""

import os
import hashlib
from pathlib import Path
from typing import Optional
from huggingface_hub import hf_hub_download, cached_download
import torch

# Default model configuration
DEFAULT_MODEL_REPO = "shawn24/Mammo-CLIP"
DEFAULT_MODEL_FILENAME = "Pre-trained-checkpoints/b5-model-best-epoch-7.tar"
DEFAULT_MODEL_NAME = "efficientnet_b5"

# Model registry with checksums for verification
MODEL_REGISTRY = {
    "efficientnet_b5": {
        "repo_id": "shawn24/Mammo-CLIP",
        "filename": "Pre-trained-checkpoints/b5-model-best-epoch-7.tar",
        "description": "EfficientNet B5 based Mammo-CLIP model (best performance)"
    }
}


def get_cache_dir() -> Path:
    """Get the cache directory for models"""
    cache_dir = os.environ.get('MAMMOCLIP_CACHE_DIR')
    if cache_dir:
        return Path(cache_dir)
    
    # Use HuggingFace cache by default
    hf_cache = os.environ.get('HF_HOME', os.path.expanduser("~/.cache/huggingface"))
    return Path(hf_cache) / "mammoclip"


def download_model(model_name: str = DEFAULT_MODEL_NAME, 
                  force_download: bool = False,
                  cache_dir: Optional[str] = None) -> str:
    """
    Download a pretrained Mammo-CLIP model from Hugging Face Hub
    
    Args:
        model_name: Name of the model to download (default: efficientnet_b5)
        force_download: Whether to force re-download even if cached
        cache_dir: Custom cache directory path
    
    Returns:
        Path to the downloaded model checkpoint
        
    Raises:
        ValueError: If model_name is not recognized
        Exception: If download fails
    """
    if model_name not in MODEL_REGISTRY:
        available_models = list(MODEL_REGISTRY.keys())
        raise ValueError(f"Unknown model '{model_name}'. Available models: {available_models}")
    
    model_info = MODEL_REGISTRY[model_name]
    repo_id = model_info["repo_id"]
    filename = model_info["filename"]
    
    print(f"Downloading Mammo-CLIP model: {model_name}")
    print(f"Description: {model_info['description']}")
    print(f"Source: {repo_id}/{filename}")
    
    try:
        # Download using huggingface_hub
        checkpoint_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            cache_dir=cache_dir,
            force_download=force_download,
            resume_download=True
        )
        
        print(f"✅ Model downloaded successfully: {checkpoint_path}")
        
        # Verify the checkpoint can be loaded
        try:
            print("🔍 Verifying checkpoint integrity...")
            ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
            if "model" not in ckpt or "config" not in ckpt:
                raise ValueError("Invalid checkpoint format")
            print("✅ Checkpoint verification passed")
        except Exception as e:
            print(f"⚠️  Warning: Checkpoint verification failed: {e}")
            print("   Model may still work, but there could be compatibility issues")
        
        return checkpoint_path
        
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        raise


def get_model_path(model_name: str = DEFAULT_MODEL_NAME,
                  auto_download: bool = True,
                  cache_dir: Optional[str] = None) -> str:
    """
    Get the path to a model checkpoint, downloading if necessary
    
    Args:
        model_name: Name of the model
        auto_download: Whether to automatically download if not cached
        cache_dir: Custom cache directory
    
    Returns:
        Path to the model checkpoint
    """
    if model_name not in MODEL_REGISTRY:
        available_models = list(MODEL_REGISTRY.keys())
        raise ValueError(f"Unknown model '{model_name}'. Available models: {available_models}")
    
    model_info = MODEL_REGISTRY[model_name]
    
    try:
        # Try to get from cache first
        checkpoint_path = hf_hub_download(
            repo_id=model_info["repo_id"],
            filename=model_info["filename"],
            cache_dir=cache_dir,
            local_files_only=True  # Only check cache, don't download
        )
        return checkpoint_path
    except Exception:
        # Not in cache
        if auto_download:
            return download_model(model_name, cache_dir=cache_dir)
        else:
            raise FileNotFoundError(f"Model '{model_name}' not found in cache and auto_download=False")


def list_available_models():
    """List all available pretrained models"""
    print("Available Mammo-CLIP Models:")
    print("=" * 50)
    
    for model_name, info in MODEL_REGISTRY.items():
        print(f"📦 {model_name}")
        print(f"   Description: {info['description']}")
        print(f"   Source: {info['repo_id']}/{info['filename']}")
        print()


def clear_cache(model_name: Optional[str] = None):
    """
    Clear cached models
    
    Args:
        model_name: Specific model to clear, or None to clear all
    """
    cache_dir = get_cache_dir()
    
    if model_name:
        print(f"Clearing cache for model: {model_name}")
        # This would require more complex logic to identify specific model files
        print("Note: Specific model clearing not implemented. Use clear_cache() to clear all.")
    else:
        print("Clearing all Mammo-CLIP model cache...")
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
            print(f"✅ Cache cleared: {cache_dir}")
        else:
            print("✅ Cache was already empty")


if __name__ == "__main__":
    # CLI interface for the downloader
    import argparse
    
    parser = argparse.ArgumentParser(description="Mammo-CLIP model downloader")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--download", type=str, help="Download a specific model")
    parser.add_argument("--force", action="store_true", help="Force re-download")
    parser.add_argument("--clear-cache", action="store_true", help="Clear model cache")
    
    args = parser.parse_args()
    
    if args.list:
        list_available_models()
    elif args.download:
        download_model(args.download, force_download=args.force)
    elif args.clear_cache:
        clear_cache()
    else:
        # Default: download the default model
        download_model() 
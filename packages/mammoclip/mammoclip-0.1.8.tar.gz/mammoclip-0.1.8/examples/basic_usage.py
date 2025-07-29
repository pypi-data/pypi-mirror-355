#!/usr/bin/env python3
"""
Basic usage example for the mammoclip package
"""

import mammoclip
import numpy as np

def main():
    """Demonstrate basic mammoclip usage"""
    
    # Path to your DICOM image
    image_path = "path/to/your/mammogram.dcm"  # Update this path
    
    print("MammoClip Basic Usage Example")
    print("=" * 40)
    
    # Method 1: Using the MammoClipModel class (automatically downloads model)
    print("\n1. Loading model (will auto-download from HuggingFace)...")
    model = mammoclip.MammoClipModel()  # No checkpoint needed!
    
    print("\n2. Encoding text prompts...")
    text_embeddings = model.encode_text(["no mass", "mass present"])
    print(f"Text embeddings shape: {text_embeddings.shape}")
    
    print("\n3. Encoding image...")
    # You can use a DICOM path, numpy array, or tensor
    image_embeddings = model.encode_image(image_path)
    print(f"Image embeddings shape: {image_embeddings.shape}")
    
    print("\n4. Computing similarity...")
    similarity = np.dot(image_embeddings, text_embeddings.T)
    print(f"Similarities: {similarity[0]}")
    
    print("\n5. Zero-shot prediction...")
    prompts_dict = {
        "mass": ["no mass", "mass present"],
        "malignancy": ["benign", "malignant"],
        "density": [
            "fatty",
            "scattered areas of fibroglandular density",
            "heterogeneously dense", 
            "extremely dense"
        ]
    }
    
    results = model.predict(image_path, prompts_dict)
    
    print("\nPrediction Results:")
    for category, result in results.items():
        print(f"  {category}: {result['prediction']} (confidence: {result['confidence']:.3f})")
    
    # Method 2: Using module-level functions
    print("\n" + "=" * 40)
    print("Alternative: Module-level functions")
    print("=" * 40)
    
    # Load model once and reuse (auto-downloads)
    model2 = mammoclip.load_model()  # No checkpoint needed!
    
    # Use convenience functions
    image_emb = mammoclip.encode_image(image_path, model=model2)
    text_emb = mammoclip.encode_text("mass present", model=model2)
    
    print(f"Image embedding shape: {image_emb.shape}")
    print(f"Text embedding shape: {text_emb.shape}")
    
    # Compute similarity
    similarity = np.dot(image_emb, text_emb.T)
    print(f"Similarity: {similarity[0][0]:.3f}")


if __name__ == "__main__":
    main() 
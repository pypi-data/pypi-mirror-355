# MammoClip

A pretrained CLIP model for mammography analysis that enables zero-shot classification and similarity search for mammographic images.

## Installation

### From PyPI (when published)
```bash
pip install mammoclip
```

### From Source
```bash
git clone https://github.com/mammoclip/mammoclip.git
cd mammoclip
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/mammoclip/mammoclip.git
cd mammoclip
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```python
import mammoclip

# Load the model
model = mammoclip.MammoClipModel("path/to/checkpoint.tar")

# Encode a DICOM image
image_embeddings = model.encode_image("path/to/mammogram.dcm")

# Encode text prompts
text_embeddings = model.encode_text(["no mass", "mass present"])

# Zero-shot prediction
prompts_dict = {
    "mass": ["no mass", "mass present"],
    "malignancy": ["benign", "malignant"],
    "density": ["fatty", "scattered areas of fibroglandular density", 
               "heterogeneously dense", "extremely dense"]
}

results = model.predict("path/to/mammogram.dcm", prompts_dict)
print(results)
```

### Module-level Functions

```python
import mammoclip

# Load model once
model = mammoclip.load_model("path/to/checkpoint.tar")

# Use convenience functions
image_emb = mammoclip.encode_image("path/to/image.dcm", model=model)
text_emb = mammoclip.encode_text("mass present", model=model)

# Compute similarity
import numpy as np
similarity = np.dot(image_emb, text_emb.T)
```

### Custom Preprocessing

```python
import mammoclip

# Manual preprocessing
processed_image = mammoclip.process_dicom_image("path/to/image.dcm")
image_tensor = mammoclip.preprocess_image(processed_image)

# Use with model
model = mammoclip.MammoClipModel("path/to/checkpoint.tar")
embeddings = model.encode_image(image_tensor)
```

## API Reference

### Classes

#### `MammoClipModel`

Main model class for mammography analysis.

**Constructor:**
- `MammoClipModel(checkpoint_path: str, device: Optional[str] = None)`

**Methods:**
- `encode_image(image)` - Encode image to embeddings
- `encode_text(text_prompts)` - Encode text prompts to embeddings  
- `predict(image, prompts_dict)` - Zero-shot prediction with multiple categories

### Functions

#### Core Functions
- `load_model(checkpoint_path, device=None)` - Load model with caching
- `encode_image(image, checkpoint_path=None, model=None)` - Module-level image encoding
- `encode_text(text_prompts, checkpoint_path=None, model=None)` - Module-level text encoding

#### Utility Functions
- `process_dicom_image(dicom_path, target_size=(912, 1520))` - Process DICOM files
- `preprocess_image(image, mean=0.3089279, std=0.25053555408335154)` - Preprocess for model

## Input Formats

### Images
- **DICOM files**: Pass file path as string
- **NumPy arrays**: Preprocessed image arrays 
- **PyTorch tensors**: Preprocessed tensors `[B, C, H, W]` or `[C, H, W]`

### Text
- **Single string**: `"mass present"`
- **List of strings**: `["no mass", "mass present"]`

## Model Requirements

- Download the pretrained checkpoint file (.tar format)
- Checkpoint should contain model weights and configuration
- Compatible with models trained with the Mammo-CLIP framework

## Dependencies

### Core Requirements
- torch>=1.9.0
- torchvision>=0.10.0
- transformers>=4.20.0
- numpy>=1.20.0
- opencv-python>=4.5.0
- scipy>=1.7.0
- dicomsdl>=0.109.0

### Optional Dependencies
```bash
# For development
pip install mammoclip[dev]

# For training
pip install mammoclip[training]
```

## Examples

See the `examples/` directory for more detailed usage examples:

- `basic_usage.py` - Basic API usage
- `batch_processing.py` - Processing multiple images
- `similarity_search.py` - Finding similar images

## License

MIT License - see LICENSE file for details.

## Citation

If you use this package in your research, please cite:

```bibtex
@article{mammoclip2024,
  title={Mammo-CLIP: A Vision Language Foundation Model to Enhance Data Efficiency and Robustness in Mammography},
  author={Your Authors},
  journal={Your Journal},
  year={2024}
}
```

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/mammoclip/mammoclip/issues)
- Documentation: [Full documentation](https://mammoclip.readthedocs.io) 
# Mammo-CLIP

**Mammo-CLIP: A Vision Language Foundation Model to Enhance Data Efficiency and Robustness in Mammography**

A pip-installable package for zero-shot mammography analysis using the Mammo-CLIP model.

## Installation

```bash
pip install mammoclip
```

## Quick Start

### Python API

```python
import mammoclip

# Initialize model (downloads automatically)
model = mammoclip.MammoClipModel()

# Analyze an image (supports DICOM, PNG, JPEG, etc.)
results = model.predict("mammogram.dcm", {
    "mass": ["no mass", "mass"],
    "malignancy": ["no malignancy", "malignancy"],
    "density": ["fatty", "scattered areas of fibroglandular density", 
               "heterogeneously dense", "extremely dense"]
})

print(results)
```

### Command Line Interface

```bash
# Basic usage
mammoclip-inference --image mammogram.dcm

# With custom prompts
mammoclip-inference --image mammogram.png --prompts custom_prompts.json
```

## Supported Image Formats

- **DICOM**: `.dcm`, `.dicom` 
- **Standard Images**: `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`

## Model Information

This package is based on the research paper:

**"Mammo-CLIP: A Vision Language Foundation Model to Enhance Data Efficiency and Robustness in Mammography"**

- **Paper**: https://arxiv.org/abs/2409.03675
- **Original Code**: https://github.com/batmanlab/Mammo-CLIP

## Citation

```bibtex
@article{shen2024mammoclip,
  title={Mammo-CLIP: A Vision Language Foundation Model to Enhance Data Efficiency and Robustness in Mammography},
  author={Shen, Shantanu and Xu, Haoyue and Weng, Jaden and Wu, Jay and Chen, Evangelia and Abbasi, Salma and Wang, Rayna and Bouzid, Hania and Rajpurkar, Pranav},
  journal={arXiv preprint arXiv:2409.03675},
  year={2024}
}
```

## License

MIT License

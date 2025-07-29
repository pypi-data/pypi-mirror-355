#!/usr/bin/env python3
"""
Setup script for mammoclip - A pretrained CLIP model for mammography
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="mammoclip",
    version="0.1.7",
    author="Mammo-CLIP Team",
    author_email="contact@mammoclip.com",
    description="A pretrained CLIP model for mammography analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mammoclip/mammoclip",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=1.9.0",
        "torchvision>=0.10.0",
        "transformers>=4.20.0",
        "numpy>=1.20.0",
        "opencv-python>=4.5.0",
        "pillow>=8.0.0",
        "scipy>=1.7.0",
        "dicomsdl>=0.109.0",
        "omegaconf>=2.1.0",
        "huggingface-hub>=0.10.0",
        "safetensors>=0.3.0",
        "albumentations>=1.0.0",
        "pandas>=1.0.0",
        "scikit-learn>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "isort>=5.0",
            "flake8>=3.8",
        ],
        "training": [
            "albumentations>=1.0.0",
            "pandas>=1.3.0",
            "scikit-learn>=1.0.0",
            "matplotlib>=3.5.0",
        ]
    },
    include_package_data=True,
    zip_safe=False,
) 
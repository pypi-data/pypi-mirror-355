#!/usr/bin/env python3
"""
Mammo-CLIP Utilities
Image processing and preprocessing functions
"""

import cv2
import torch
import numpy as np
import dicomsdl
from typing import Tuple
from pathlib import Path


def np_CountUpContinuingOnes(b_arr):
    """Count continuing ones from left and right side"""
    left = np.arange(len(b_arr))
    left[b_arr > 0] = 0
    left = np.maximum.accumulate(left)

    rev_arr = b_arr[::-1]
    right = np.arange(len(rev_arr))
    right[rev_arr > 0] = 0
    right = np.maximum.accumulate(right)
    right = len(rev_arr) - 1 - right[::-1]

    return right - left - 1


def extract_breast(img: np.ndarray) -> np.ndarray:
    """
    Extract breast region from mammogram
    
    Args:
        img: Input mammogram image
    
    Returns:
        Extracted breast region
    """
    img_copy = img.copy()
    img = np.where(img <= 40, 0, img)  # To detect backgrounds easily
    height, _ = img.shape

    # whether each col is non-constant or not
    y_a = height // 2 + int(height * 0.4)
    y_b = height // 2 - int(height * 0.4)
    b_arr = img[y_b:y_a].std(axis=0) != 0
    continuing_ones = np_CountUpContinuingOnes(b_arr)
    # longest should be the breast
    col_ind = np.where(continuing_ones == continuing_ones.max())[0]
    img = img[:, col_ind]

    # whether each row is non-constant or not
    _, width = img.shape
    x_a = width // 2 + int(width * 0.4)  
    x_b = width // 2 - int(width * 0.4)
    b_arr = img[:, x_b:x_a].std(axis=1) != 0
    continuing_ones = np_CountUpContinuingOnes(b_arr)
    # longest should be the breast
    row_ind = np.where(continuing_ones == continuing_ones.max())[0]

    return img_copy[row_ind][:, col_ind]


def process_image(image_path: str, target_size: Tuple[int, int] = (912, 1520)) -> np.ndarray:
    """
    Process medical image (DICOM, PNG, JPEG, etc.) to match preprocessing used in training
    
    Args:
        image_path: Path to image file (supports .dcm, .dicom, .png, .jpg, .jpeg, .tiff, .bmp)
        target_size: Target size for resizing (width, height)
    
    Returns:
        Processed image as numpy array
    """
    image_path = Path(image_path)
    file_extension = image_path.suffix.lower()
    
    print(f"Processing image: {image_path}")
    
    # Determine file type and load accordingly
    if file_extension in ['.dcm', '.dicom']:
        # Load DICOM
        dicom = dicomsdl.open(str(image_path))
        data = dicom.pixelData()
        data = data[5:-5, 5:-5]  # Remove border
        
        # Handle MONOCHROME1
        if dicom.getPixelDataInfo()['PhotometricInterpretation'] == "MONOCHROME1":
            data = np.amax(data) - data
        
        # Normalize to 0-255
        data = data - np.min(data)
        data = data / np.max(data)
        data = (data * 255).astype(np.uint8)
        
    elif file_extension in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp']:
        # Load standard image formats
        data = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if data is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Ensure proper data type and range
        if data.dtype != np.uint8:
            # Normalize to 0-255 range
            data = data - np.min(data)
            data = data / np.max(data)
            data = (data * 255).astype(np.uint8)
    
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. "
                        f"Supported formats: .dcm, .dicom, .png, .jpg, .jpeg, .tiff, .bmp")
    
    # Extract breast region (works for both DICOM and standard images)
    img = extract_breast(data)
    
    # Resize to target size
    img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
    
    return img


def process_dicom_image(dicom_path: str, target_size: Tuple[int, int] = (912, 1520)) -> np.ndarray:
    """
    Process DICOM image (legacy function for backward compatibility)
    
    Args:
        dicom_path: Path to DICOM file
        target_size: Target size for resizing (width, height)
    
    Returns:
        Processed image as numpy array
    """
    return process_image(dicom_path, target_size)


def preprocess_image(image: np.ndarray, 
                    mean: float = 0.3089279, 
                    std: float = 0.25053555408335154) -> torch.Tensor:
    """
    Convert image to tensor and normalize for model input
    
    Args:
        image: Input image as numpy array
        mean: Normalization mean
        std: Normalization standard deviation
    
    Returns:
        Preprocessed image tensor [1, 3, H, W]
    """
    # Convert to float and normalize to [0, 1]
    image = image.astype(np.float32) / 255.0
    
    # Normalize with dataset statistics
    image = (image - mean) / std
    
    # Convert to tensor and add batch dimension
    image_tensor = torch.FloatTensor(image).unsqueeze(0)  # [1, H, W]
    
    # Convert grayscale to 3-channel by repeating channel 3 times
    image_tensor = image_tensor.repeat(3, 1, 1).unsqueeze(0)  # [1, 3, H, W]
    
    return image_tensor 
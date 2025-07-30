"""
Utility functions for brain-striatum segmentation
"""

import logging
from pathlib import Path
from typing import Union
import nibabel as nib

def validate_input_file(file_path: Union[str, Path]) -> Path:
    """Validate that input file exists and is a NIfTI file"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    if not (file_path.suffix.lower() == '.gz' and file_path.stem.endswith('.nii')):
        raise ValueError(f"Input must be a .nii.gz file, got: {file_path}")
    
    return file_path

def setup_logging(verbose: bool = True):
    """Setup logging configuration"""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def load_nifti_safe(file_path: Union[str, Path]) -> nib.Nifti1Image:
    """Safely load a NIfTI image with error handling"""
    try:
        return nib.load(str(file_path))
    except Exception as e:
        raise RuntimeError(f"Failed to load NIfTI image {file_path}: {e}")

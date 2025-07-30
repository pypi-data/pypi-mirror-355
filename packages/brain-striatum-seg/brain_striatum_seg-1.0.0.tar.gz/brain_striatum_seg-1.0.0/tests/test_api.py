"""
Tests for brain_striatum_seg API
"""

import pytest
import tempfile
from pathlib import Path
import nibabel as nib
import numpy as np

from brain_striatum_seg import brain_striatum_segmentation

def create_dummy_pet_image():
    """Create a dummy PET image for testing"""
    # Create dummy 3D image data
    data = np.random.rand(64, 64, 32) * 1000
    
    # Create NIfTI image
    img = nib.Nifti1Image(data, np.eye(4))
    
    return img

def test_api_imports():
    """Test that the API can be imported"""
    from brain_striatum_seg import brain_striatum_segmentation
    assert callable(brain_striatum_segmentation)

# Add more tests as needed

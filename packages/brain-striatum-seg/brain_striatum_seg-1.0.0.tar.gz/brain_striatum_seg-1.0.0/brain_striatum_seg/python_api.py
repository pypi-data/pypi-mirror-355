"""
Python API for Brain-Striatum Segmentation
Following TotalSegmentator's API pattern
"""

import nibabel as nib
from pathlib import Path
from typing import Union, Optional
from nibabel.nifti1 import Nifti1Image

from .predictor import BrainStriatumPredictor
from .config import setup_directories

def brain_striatum_segmentation(
    input_path: Union[str, Path, Nifti1Image],
    output_path: Union[str, Path, None] = None,
    device: str = "auto",
    verbose: bool = True,
    fast: bool = False,
    tile_step_size: float = 0.5,
    use_gaussian: bool = True
) -> Union[Nifti1Image, None]:
    """
    Main API function for brain-striatum segmentation.
    
    Args:
        input_path: Input PET image (.nii.gz file) or nibabel image object
        output_path: Output directory or file path. If None, returns nibabel image
        device: Device to use ('auto', 'cpu', 'cuda', 'gpu')
        verbose: Print progress information
        fast: Use faster settings (larger tile step size)
        tile_step_size: Step size for tiled prediction
        use_gaussian: Use Gaussian smoothing
        
    Returns:
        If output_path is None, returns nibabel image object
        Otherwise returns None and saves result to output_path
        
    Examples:
        # Save to file
        brain_striatum_segmentation("input.nii.gz", "output_dir/")
        
        # Return as nibabel image
        result_img = brain_striatum_segmentation("input.nii.gz")
        
        # Use nibabel image as input
        input_img = nib.load("input.nii.gz")
        result_img = brain_striatum_segmentation(input_img)
    """
    
    # Setup
    setup_directories()
    
    if verbose:
        print("\\n" + "="*50)
        print("🧠 Brain-Striatum Segmentation v1.0.0")
        print("="*50)
    
    # Handle fast mode
    if fast:
        tile_step_size = 1.0  # Larger step size for speed
    
    # Handle device
    if device == "auto":
        device = None  # Let predictor auto-detect
    
    # Initialize predictor
    predictor = BrainStriatumPredictor(
        device=device,
        use_gaussian=use_gaussian,
        tile_step_size=tile_step_size,
        verbose=verbose
    )
    
    # Handle input
    if isinstance(input_path, Nifti1Image):
        # Save nibabel image to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp:
            nib.save(input_path, tmp.name)
            input_file = Path(tmp.name)
            temp_input = True
    else:
        input_file = Path(input_path)
        temp_input = False
    
    # Handle output
    if output_path is None:
        # Return nibabel image
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            result_file = predictor.predict_single(input_file, temp_dir)
            result_img = nib.load(result_file)
        
        if temp_input:
            input_file.unlink()  # Clean up temp input
        
        return result_img
    
    else:
        # Save to file/directory
        output_path = Path(output_path)
        if output_path.is_dir() or not output_path.suffix:
            # Directory provided
            result_file = predictor.predict_single(input_file, output_path)
        else:
            # Specific file path provided
            temp_dir = output_path.parent
            result_file = predictor.predict_single(input_file, temp_dir)
            # Move/rename to desired location
            result_file.rename(output_path)
        
        if temp_input:
            input_file.unlink()  # Clean up temp input
        
        if verbose:
            print(f"\\n✅ Results saved to: {output_path}")
        
        return None

# Backwards compatibility alias
totalsegmentator = brain_striatum_segmentation

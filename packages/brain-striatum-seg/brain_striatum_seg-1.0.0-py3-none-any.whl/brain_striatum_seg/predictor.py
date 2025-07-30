import tempfile
import shutil
import logging
import os
from pathlib import Path
import torch
import nibabel as nib
import numpy as np
from typing import Union, Optional

from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor

from .config import get_models_dir, setup_directories
from .download import download_model

logger = logging.getLogger(__name__)

class BrainStriatumPredictor:
    """
    Main predictor class for the two-stage brain-striatum segmentation pipeline.
    """
    
    def __init__(self, 
                 device: Optional[str] = None,
                 use_gaussian: bool = True,
                 tile_step_size: float = 0.5,
                 verbose: bool = True):
        
        # Setup directories
        setup_directories()
        
        # Setup nnUNet environment variables to avoid warnings
        self._setup_nnunet_env()
        
        # Device setup
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        elif device == "gpu":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = torch.device(device)
        self.use_gaussian = use_gaussian
        self.tile_step_size = tile_step_size
        self.verbose = verbose
        
        # Initialize predictors (loaded lazily)
        self.brain_predictor = None
        self.striatum_predictor = None
        
        if verbose:
            print(f"🧠 Brain-Striatum Predictor initialized on {self.device}")
    
    def _setup_nnunet_env(self):
        """Setup nnUNet environment variables to avoid warnings."""
        models_dir = get_models_dir()
        
        # Set nnUNet environment variables if not already set
        if "nnUNet_raw" not in os.environ:
            os.environ["nnUNet_raw"] = str(models_dir / "nnUNet_raw")
        if "nnUNet_preprocessed" not in os.environ:
            os.environ["nnUNet_preprocessed"] = str(models_dir / "nnUNet_preprocessed")
        if "nnUNet_results" not in os.environ:
            os.environ["nnUNet_results"] = str(models_dir / "nnUNet_results")
    
    def _ensure_model_downloaded(self, model_name):
        """Ensure model is downloaded before use."""
        models_dir = get_models_dir()
        model_dir = models_dir / model_name
        
        if not model_dir.exists():
            print(f"📥 {model_name} not found. Downloading...")
            download_model(model_name)
        
        return model_dir
    
    def _load_brain_predictor(self):
        """Load brain extraction model."""
        if self.brain_predictor is None:
            model_dir = self._ensure_model_downloaded("brain_model")
            
            # Initialize predictor with simplified parameters
            self.brain_predictor = nnUNetPredictor(
                tile_step_size=self.tile_step_size,
                use_gaussian=self.use_gaussian,
                use_mirroring=True,
                device=self.device,
                verbose=self.verbose
            )
            
            try:
                self.brain_predictor.initialize_from_trained_model_folder(
                    str(model_dir),
                    use_folds='all',
                    checkpoint_name="checkpoint_best.pth"
                )
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Warning: {e}")
                    print("🔄 Trying with checkpoint_final.pth...")
                # Fallback to final checkpoint
                self.brain_predictor.initialize_from_trained_model_folder(
                    str(model_dir),
                    use_folds='all',
                    checkpoint_name="checkpoint_final.pth"
                )
            
            if self.verbose:
                print("✅ Brain extraction model loaded")
    
    def _load_striatum_predictor(self):
        """Load striatum segmentation model."""
        if self.striatum_predictor is None:
            model_dir = self._ensure_model_downloaded("striatum_model")
            
            # Initialize predictor with simplified parameters
            self.striatum_predictor = nnUNetPredictor(
                tile_step_size=self.tile_step_size,
                use_gaussian=self.use_gaussian,
                use_mirroring=True,
                device=self.device,
                verbose=self.verbose
            )
            
            try:
                self.striatum_predictor.initialize_from_trained_model_folder(
                    str(model_dir),
                    use_folds='all',
                    checkpoint_name="checkpoint_best.pth"
                )
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Warning: {e}")
                    print("🔄 Trying with checkpoint_final.pth...")
                # Fallback to final checkpoint
                self.striatum_predictor.initialize_from_trained_model_folder(
                    str(model_dir),
                    use_folds='all',
                    checkpoint_name="checkpoint_final.pth"
                )
            
            if self.verbose:
                print("✅ Striatum segmentation model loaded")
    
    def predict_single(self, input_file: Union[str, Path], output_dir: Union[str, Path]) -> Path:
        """Predict brain and striatum segmentation for a single PET image."""
        input_file = Path(input_file).resolve()  # Get absolute path
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate input file
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        if not str(input_file).endswith('.nii.gz'):
            raise ValueError(f"Input file must be .nii.gz format: {input_file}")
        
        if self.verbose:
            print(f"🔄 Processing: {input_file.name}")
            print(f"📂 Full path: {input_file}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            # Stage 1: Brain extraction
            if self.verbose:
                print("🧠 Stage 1: Brain extraction")
            self._load_brain_predictor()
            
            brain_mask_dir = temp_dir / "brain_masks"
            brain_mask_dir.mkdir()
            
            # Create input directory with proper structure for nnUNet
            input_temp_dir = temp_dir / "input"
            input_temp_dir.mkdir()
            
            # Copy input file to temp directory with proper naming
            temp_input_file = input_temp_dir / input_file.name
            shutil.copy2(input_file, temp_input_file)
            
            if self.verbose:
                print(f"📁 Temp input: {temp_input_file}")
                print(f"📁 Output dir: {brain_mask_dir}")
            
            try:
                # Use the temp input directory
                self.brain_predictor.predict_from_files(
                    list_of_lists_or_source_folder=str(input_temp_dir),
                    output_folder_or_list_of_truncated_output_files=str(brain_mask_dir),
                    save_probabilities=False,
                    overwrite=True,
                    num_processes_preprocessing=1,
                    num_processes_segmentation_export=1
                )
            except Exception as e:
                if self.verbose:
                    print(f"❌ Brain extraction failed: {e}")
                    print("🔄 Trying alternative approach...")
                
                # Alternative: predict single file directly
                self.brain_predictor.predict_from_files(
                    list_of_lists_or_source_folder=[[str(temp_input_file)]],
                    output_folder_or_list_of_truncated_output_files=str(brain_mask_dir),
                    save_probabilities=False,
                    overwrite=True,
                    num_processes_preprocessing=1,
                    num_processes_segmentation_export=1
                )
            
            # Find brain mask
            brain_mask_files = list(brain_mask_dir.glob("*.nii.gz"))
            if not brain_mask_files:
                raise RuntimeError(f"No brain mask files found in {brain_mask_dir}")
            brain_mask_file = brain_mask_files[0]
            
            if self.verbose:
                print(f"✅ Brain mask created: {brain_mask_file.name}")
            
            # Stage 2: Apply brain mask
            if self.verbose:
                print("✂️  Stage 2: Brain cropping")
            brain_cropped_file = self._apply_brain_mask(temp_input_file, brain_mask_file, temp_dir)
            
            # Stage 3: Striatum segmentation
            if self.verbose:
                print("🎯 Stage 3: Striatum segmentation")
            self._load_striatum_predictor()
            
            striatum_seg_dir = temp_dir / "striatum_seg"
            striatum_seg_dir.mkdir()
            
            # Create input directory for striatum model
            striatum_input_dir = temp_dir / "striatum_input"
            striatum_input_dir.mkdir()
            striatum_temp_file = striatum_input_dir / brain_cropped_file.name
            shutil.copy2(brain_cropped_file, striatum_temp_file)
            
            try:
                self.striatum_predictor.predict_from_files(
                    list_of_lists_or_source_folder=str(striatum_input_dir),
                    output_folder_or_list_of_truncated_output_files=str(striatum_seg_dir),
                    save_probabilities=False,
                    overwrite=True,
                    num_processes_preprocessing=1,
                    num_processes_segmentation_export=1
                )
            except Exception as e:
                if self.verbose:
                    print(f"❌ Striatum segmentation failed: {e}")
                    print("🔄 Trying alternative approach...")
                
                # Alternative approach
                self.striatum_predictor.predict_from_files(
                    list_of_lists_or_source_folder=[[str(striatum_temp_file)]],
                    output_folder_or_list_of_truncated_output_files=str(striatum_seg_dir),
                    save_probabilities=False,
                    overwrite=True,
                    num_processes_preprocessing=1,
                    num_processes_segmentation_export=1
                )
            
            # Save final result
            striatum_seg_files = list(striatum_seg_dir.glob("*.nii.gz"))
            if not striatum_seg_files:
                raise RuntimeError(f"No striatum segmentation files found in {striatum_seg_dir}")
            striatum_seg_file = striatum_seg_files[0]
            
            final_output = output_dir / f"{input_file.stem.replace('.nii', '')}_striatum_seg.nii.gz"
            shutil.copy2(striatum_seg_file, final_output)
        
        if self.verbose:
            print(f"✅ Completed: {final_output}")
        
        return final_output
    
    def _apply_brain_mask(self, original_file: Path, mask_file: Path, temp_dir: Path) -> Path:
        """Apply brain mask to original PET image."""
        original_img = nib.load(original_file)
        mask_img = nib.load(mask_file)
        
        original_data = original_img.get_fdata()
        mask_data = mask_img.get_fdata()
        
        # Apply mask
        brain_cropped_data = original_data * (mask_data > 0)
        
        # Create new image
        brain_cropped_img = nib.Nifti1Image(
            brain_cropped_data,
            original_img.affine,
            original_img.header
        )
        
        # Save
        brain_cropped_file = temp_dir / f"{original_file.stem.replace('.nii', '')}_brain_cropped.nii.gz"
        nib.save(brain_cropped_img, brain_cropped_file)
        
        return brain_cropped_file
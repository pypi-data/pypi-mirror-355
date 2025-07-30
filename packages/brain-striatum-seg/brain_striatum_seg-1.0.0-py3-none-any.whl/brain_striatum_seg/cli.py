#!/usr/bin/env python3
"""
Command-line interface for Brain-Striatum Segmentation
Following TotalSegmentator's CLI pattern
"""

import argparse
import sys
from pathlib import Path

from .python_api import brain_striatum_segmentation

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Brain-Striatum Segmentation: Automated brain and striatum segmentation from PET images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file
  brain-striatum-seg -i input.nii.gz -o output_dir/
  
  # Process multiple files
  brain-striatum-seg -i input_dir/ -o output_dir/
  
  # Fast mode (lower accuracy, faster runtime)
  brain-striatum-seg -i input.nii.gz -o output_dir/ --fast
  
  # Use CPU instead of GPU
  brain-striatum-seg -i input.nii.gz -o output_dir/ --device cpu

Citation:
  If you use this tool, please cite our paper: [Your Citation]
  Please also cite nnUNet: https://github.com/MIC-DKFZ/nnUNet
        """
    )
    
    parser.add_argument(
        "-i", "--input", 
        type=str, 
        required=True,
        help="Input PET image (.nii.gz) or directory containing images"
    )
    
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        required=True,
        help="Output directory for segmentation results"
    )
    
    parser.add_argument(
        "--device", 
        type=str, 
        default="auto",
        choices=["auto", "cpu", "gpu", "cuda"],
        help="Device for inference (default: auto)"
    )
    
    parser.add_argument(
        "--fast", 
        action="store_true",
        help="Fast mode (lower accuracy, faster runtime)"
    )
    
    parser.add_argument(
        "--tile-step-size", 
        type=float, 
        default=0.5,
        help="Step size for tiled prediction (default: 0.5)"
    )
    
    parser.add_argument(
        "--no-gaussian", 
        action="store_true",
        help="Disable Gaussian smoothing"
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        default=True,
        help="Verbose output (default: True)"
    )
    
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Quiet mode (disable verbose output)"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="brain-striatum-seg 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Handle verbose/quiet
    verbose = args.verbose and not args.quiet
    
    try:
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        if input_path.is_file():
            # Single file
            brain_striatum_segmentation(
                input_path=input_path,
                output_path=output_path,
                device=args.device,
                verbose=verbose,
                fast=args.fast,
                tile_step_size=args.tile_step_size,
                use_gaussian=not args.no_gaussian
            )
        
        elif input_path.is_dir():
            # Multiple files
            input_files = list(input_path.glob("*.nii.gz"))
            if not input_files:
                print(f"❌ No .nii.gz files found in {input_path}")
                return 1
            
            if verbose:
                print(f"🔄 Processing {len(input_files)} files...")
            
            for input_file in input_files:
                try:
                    brain_striatum_segmentation(
                        input_path=input_file,
                        output_path=output_path,
                        device=args.device,
                        verbose=verbose,
                        fast=args.fast,
                        tile_step_size=args.tile_step_size,
                        use_gaussian=not args.no_gaussian
                    )
                except Exception as e:
                    print(f"❌ Failed to process {input_file}: {e}")
                    continue
        
        else:
            print(f"❌ Input path does not exist: {input_path}")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

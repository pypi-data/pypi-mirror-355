import os
import requests
import zipfile
from pathlib import Path
from tqdm import tqdm
import argparse

from .config import get_models_dir, get_model_urls, update_config, get_config

def download_file(url, destination, show_progress=True):
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(destination, 'wb') as f:
        if show_progress and total_size > 0:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Downloading {destination.name}") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        else:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

def extract_model(zip_path, models_dir, model_name):
    """Extract model zip file to the correct directory structure."""
    print(f"📦 Extracting {model_name} model...")
    
    # Create the specific model directory
    model_dir = models_dir / model_name
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(model_dir)
    
    # Check if extraction created a nested directory and flatten if needed
    extracted_contents = list(model_dir.iterdir())
    if len(extracted_contents) == 1 and extracted_contents[0].is_dir():
        # If there's only one directory, move its contents up one level
        nested_dir = extracted_contents[0]
        for item in nested_dir.iterdir():
            item.rename(model_dir / item.name)
        nested_dir.rmdir()
    
    # Remove zip file after extraction
    zip_path.unlink()
    
    print(f"✅ Extracted to: {model_dir}")
    return model_dir

def is_model_complete(model_dir):
    """Check if a model directory contains all necessary files."""
    model_dir = Path(model_dir)
    
    if not model_dir.exists():
        return False
    
    # Check for essential nnUNet files
    required_files = [
        "plans.json",
        "dataset.json"
    ]
    
    # Check for fold directories or checkpoint files
    has_folds = any(item.name.startswith("fold_") for item in model_dir.iterdir() if item.is_dir())
    has_checkpoints = any(item.name.endswith(".pth") for item in model_dir.rglob("*.pth"))
    
    # Check required files exist
    for req_file in required_files:
        if not (model_dir / req_file).exists():
            print(f"❌ Missing required file: {req_file}")
            return False
    
    if not (has_folds or has_checkpoints):
        print(f"❌ No model weights found (no fold directories or .pth files)")
        return False
    
    return True

def download_model(model_name, force_download=False):
    """Download a specific model."""
    models_dir = get_models_dir()
    model_urls = get_model_urls()
    config = get_config()
    
    if model_name not in model_urls:
        raise ValueError(f"Unknown model: {model_name}. Available models: {list(model_urls.keys())}")
    
    model_info = model_urls[model_name]
    model_dir = models_dir / model_name
    
    # Check if model already exists and is complete
    if not force_download:
        if is_model_complete(model_dir):
            print(f"✅ Model '{model_name}' already downloaded and complete")
            return model_dir
        elif model_dir.exists():
            print(f"🔄 Model '{model_name}' directory exists but incomplete, re-downloading...")
            import shutil
            shutil.rmtree(model_dir)
    
    print(f"📥 Downloading {model_name} model ({model_info['size_mb']}MB)...")
    
    # Create models directory
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Download model
    zip_path = models_dir / model_info["filename"]
    
    # Remove existing zip if it exists
    if zip_path.exists():
        zip_path.unlink()
    
    download_file(model_info["url"], zip_path)
    
    # Extract model
    final_model_dir = extract_model(zip_path, models_dir, model_name)
    
    # Verify extraction was successful
    if not is_model_complete(final_model_dir):
        raise RuntimeError(f"Model extraction failed or model is incomplete: {final_model_dir}")
    
    # Update config
    models_downloaded = config.get("models_downloaded", {})
    models_downloaded[model_name] = True
    update_config("models_downloaded", models_downloaded)
    
    print(f"✅ {model_name} model downloaded and ready!")
    print(f"📂 Model location: {final_model_dir}")
    
    return final_model_dir

def download_all_models(force_download=False):
    """Download all required models."""
    model_urls = get_model_urls()
    for model_name in model_urls.keys():
        download_model(model_name, force_download)

def download_weights_cli():
    """CLI for downloading model weights."""
    parser = argparse.ArgumentParser(description="Download brain-striatum segmentation model weights")
    parser.add_argument("-m", "--model", choices=["brain_model", "striatum_model", "all"], 
                       default="all", help="Model to download")
    parser.add_argument("--force", action="store_true", help="Force re-download even if model exists")
    
    args = parser.parse_args()
    
    try:
        if args.model == "all":
            download_all_models(args.force)
        else:
            download_model(args.model, args.force)
    except Exception as e:
        print(f"❌ Error downloading models: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(download_weights_cli())
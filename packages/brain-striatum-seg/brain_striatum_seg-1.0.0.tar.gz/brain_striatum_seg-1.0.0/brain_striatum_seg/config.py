import os
import json
from pathlib import Path
import pkg_resources

def get_brainstriatum_dir():
    """Get the main directory for brain-striatum-seg configuration and models."""
    if "BRAINSTRIATUM_HOME_DIR" in os.environ:
        return Path(os.environ["BRAINSTRIATUM_HOME_DIR"])
    else:
        # Follow TotalSegmentator pattern
        home_path = Path("/tmp") if str(Path.home()) == "/" else Path.home()
        return home_path / ".brain_striatum_seg"

def get_models_dir():
    """Get the directory where models are stored."""
    if "BRAINSTRIATUM_MODELS_PATH" in os.environ:
        return Path(os.environ["BRAINSTRIATUM_MODELS_PATH"])
    else:
        return get_brainstriatum_dir() / "models"

def setup_directories():
    """Create necessary directories."""
    models_dir = get_models_dir()
    models_dir.mkdir(parents=True, exist_ok=True)
    
    config_dir = get_brainstriatum_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create config file if it doesn't exist
    config_file = config_dir / "config.json"
    if not config_file.exists():
        default_config = {
            "version": "1.0.0",
            "models_downloaded": {},
            "usage_stats": True,
            "first_run": True
        }
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=4)

def get_config():
    """Read configuration file."""
    config_file = get_brainstriatum_dir() / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)
    return {}

def update_config(key, value):
    """Update configuration file."""
    config_file = get_brainstriatum_dir() / "config.json"
    config = get_config()
    config[key] = value
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)

def get_model_urls():
    """Get model download URLs."""
    try:
        urls_file = pkg_resources.resource_filename(
            'brain_striatum_seg', 
            'resources/model_urls.json'
        )
        with open(urls_file) as f:
            return json.load(f)
    except Exception:
        # Fallback URLs (you'll replace these with your actual model URLs)
        return {
            "brain_model": {
                "url": "https://your-server.com/models/brain_model.zip",
                "filename": "brain_model.zip",
                "size_mb": 250
            },
            "striatum_model": {
                "url": "https://your-server.com/models/striatum_model.zip", 
                "filename": "striatum_model.zip",
                "size_mb": 180
            }
        }

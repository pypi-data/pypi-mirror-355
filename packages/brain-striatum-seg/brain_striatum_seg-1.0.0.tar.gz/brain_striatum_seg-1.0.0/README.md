# Brain-Striatum Segmentation

[![PyPI version](https://badge.fury.io/py/brain-striatum-seg.svg)](https://badge.fury.io/py/brain-striatum-seg)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Automated brain and striatum segmentation from PET images using cascaded nnUNet models.

## 🧠 Overview

This package implements a two-stage segmentation pipeline:

1. **Brain Extraction**: Segments the brain region from PET images
2. **Brain Cropping**: Applies the brain mask to focus on brain tissue  
3. **Striatum Segmentation**: Segments the striatum from brain-cropped images

## 📦 Installation

```bash
pip install brain-striatum-seg
```

## 🚀 Quick Start

### Command Line Interface
```bash
# Process single file
brain-striatum-seg -i input.nii.gz -o output_dir/

# Process multiple files
brain-striatum-seg -i input_directory/ -o output_directory/
```

### Python API
```python
from brain_striatum_seg import brain_striatum_segmentation

# Process and save to file
brain_striatum_segmentation("input.nii.gz", "output_dir/")

# Return nibabel image
result_img = brain_striatum_segmentation("input.nii.gz")
```

## 📚 Documentation

- **Input**: PET images in NIfTI format (`.nii.gz`)
- **Output**: Binary segmentation masks (`.nii.gz`)

## 📄 Citation

If you use this tool in your research, please cite our paper: [Your Citation Here]

Please also cite nnUNet: https://github.com/MIC-DKFZ/nnUNet

## 📜 License

Apache License 2.0

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

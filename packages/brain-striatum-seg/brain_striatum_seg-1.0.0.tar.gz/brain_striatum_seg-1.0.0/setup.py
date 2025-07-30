from setuptools import setup, find_packages

def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="brain-striatum-seg",
    version="1.0.0",
    author="Bong-il Song,Yeaeun Song", 
    author_email="nuclesong@gmail.com, itscarolinesong@gmail.com",
    description="Automated brain and striatum segmentation from PET images using cascaded nnUNet models",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    license="Apache 2.0",
    packages=find_packages(),
    package_data={
        "brain_striatum_seg": [
            "resources/model_urls.json",
        ],
    },
    python_requires=">=3.8,<3.12",  # Updated Python requirement
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "brain-striatum-seg=brain_striatum_seg.cli:main",
            "brainstriatum_download_weights=brain_striatum_seg.download:download_weights_cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    project_urls={
        "Bug Reports": "https://github.com/itscarolinesong/brain-striatum-seg/issues",  
        "Models": "https://zenodo.org/records/15662802",  # UPDATE WITH YOUR ZENODO
        "Documentation": "https://pypi.org/project/brain-striatum-seg/",
    },
)

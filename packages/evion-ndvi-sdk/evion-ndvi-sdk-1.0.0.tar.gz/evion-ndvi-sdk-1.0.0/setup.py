from setuptools import setup, find_packages
import os

# Read README file
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "EvionAI NDVI SDK - Python library for crop image NDVI prediction"

setup(
    name="evion-ndvi-sdk",
    version="1.0.0",
    author="EvionAI",
    author_email="support@evionai.com",
    description="Python SDK for EvionAI NDVI prediction service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/evionai/evion-ndvi-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers", 
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "Pillow>=8.0.0", 
        "numpy>=1.19.0",
        "matplotlib>=3.3.0",
    ],
    entry_points={
        "console_scripts": [
            "evion-ndvi=evion_ndvi_sdk.cli:main",
        ],
    },
) 
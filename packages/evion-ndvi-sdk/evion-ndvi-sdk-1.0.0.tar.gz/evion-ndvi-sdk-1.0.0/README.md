# EvionAI NDVI SDK

🌾 **A simple Python library for generating NDVI predictions from crop images using EvionAI's machine learning models.**

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

The EvionAI NDVI SDK allows researchers, developers, and agricultural professionals to easily upload crop images and receive synthetic NDVI (Normalized Difference Vegetation Index) predictions. With just a few lines of code, you can integrate powerful crop health analysis into your applications.

## Features

- 🚀 **Simple API**: Just 3 lines of code to get NDVI predictions
- 📁 **Multiple Input Formats**: Support for .tif, .tiff, .jpg, .png files
- 💾 **Automatic Downloads**: Results automatically saved to your preferred location
- 🔧 **Command Line Interface**: Use from terminal for quick analysis
- 🔒 **Secure Authentication**: API key-based authentication
- 📊 **Rich Results**: High-quality NDVI visualizations with color mapping

## Installation

```bash
pip install evion-ndvi-sdk
```

## Quick Start

### 1. Get Your API Key

First, you need an API key from EvionAI:

1. Visit [https://platform.evionai.com](https://platform.evionai.com)
2. Sign up or log in to your account
3. Navigate to your dashboard
4. Create a new API key
5. Copy the API key for use in your code

### 2. Basic Usage

```python
from evion_ndvi_sdk import EvionNDVI

# Initialize the client with your API key
client = EvionNDVI(api_key="your_api_key_here")

# Generate NDVI prediction from an image file
result = client.predict_from_file("path/to/your/crop_image.jpg")

# The result image is automatically downloaded as 'crop_image_ndvi.png'
print(f"Prediction completed for image: {result.image_id}")
```

That's it! Your NDVI prediction will be automatically saved as a PNG image.

## Detailed Usage

### Working with Files

```python
from evion_ndvi_sdk import EvionNDVI

client = EvionNDVI(api_key="your_api_key_here")

# Predict from a specific file
result = client.predict_from_file(
    image_path="field_photo.tif",
    auto_download=True,  # Automatically save result
    download_dir="./results"  # Custom download directory
)

# Manually save to a specific location
result.save_image("custom_ndvi_result.png")
```

### Working with Image Data

```python
# If you have image data in memory
with open("crop.jpg", "rb") as f:
    image_bytes = f.read()

result = client.predict_from_bytes(
    image_data=image_bytes,
    filename="my_crop",
    download_dir="./output"
)
```

### Random Sample Predictions

```python
# Generate prediction using a random sample image
result = client.predict_random(download_dir="./samples")
print(f"Random sample ID: {result.image_id}")
```

### Advanced Configuration

```python
# Custom API endpoint (for enterprise users)
client = EvionNDVI(
    api_key="your_api_key",
    base_url="https://api.evionai.com"  # Custom endpoint
)

# Test your connection
if client.test_connection():
    print("✅ Connected successfully!")
else:
    print("❌ Connection failed")
```

## Command Line Interface

The SDK includes a command-line tool for quick analysis:

```bash
# Test your API key
evion-ndvi --api-key YOUR_API_KEY --test

# Analyze a specific image
evion-ndvi --api-key YOUR_API_KEY --image crop.jpg

# Generate random prediction
evion-ndvi --api-key YOUR_API_KEY --random

# Save to specific directory
evion-ndvi --api-key YOUR_API_KEY --image field.tif --output-dir ./results

# Don't auto-download (just get the result object)
evion-ndvi --api-key YOUR_API_KEY --image crop.png --no-download
```

## Error Handling

```python
from evion_ndvi_sdk import EvionNDVI, AuthenticationError, RateLimitError, APIError

client = EvionNDVI(api_key="your_api_key")

try:
    result = client.predict_from_file("crop.jpg")
except AuthenticationError:
    print("Invalid API key. Please check your credentials.")
except RateLimitError:
    print("Rate limit exceeded. Please try again later.")
except APIError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Complete Example

```python
from evion_ndvi_sdk import EvionNDVI
from pathlib import Path

def analyze_crop_field(image_path, api_key):
    """Analyze a crop field image and return NDVI results"""
    
    # Initialize client
    client = EvionNDVI(api_key=api_key)
    
    # Test connection first
    if not client.test_connection():
        raise Exception("Cannot connect to EvionAI API")
    
    # Generate prediction
    result = client.predict_from_file(
        image_path=image_path,
        auto_download=True,
        download_dir="./ndvi_results"
    )
    
    print(f"✅ Analysis complete!")
    print(f"   Image ID: {result.image_id}")
    print(f"   Has ground truth: {result.has_ground_truth}")
    
    return result

# Usage
if __name__ == "__main__":
    api_key = "your_api_key_here"
    result = analyze_crop_field("my_field.tif", api_key)
```

## Supported Image Formats

- **TIFF/TIF**: Recommended for satellite/drone imagery
- **JPEG/JPG**: Standard photo format
- **PNG**: Lossless image format

## API Reference

### EvionNDVI Class

#### `__init__(api_key: str, base_url: str = "http://localhost:8000")`
Initialize the EvionAI client.

#### `predict_from_file(image_path, auto_download=True, download_dir=None) -> NDVIResult`
Generate NDVI prediction from an image file.

#### `predict_from_bytes(image_data, filename="image", auto_download=True, download_dir=".") -> NDVIResult`
Generate NDVI prediction from image bytes.

#### `predict_random(auto_download=True, download_dir=".") -> NDVIResult`
Generate NDVI prediction using a random sample image.

#### `test_connection() -> bool`
Test connection to the EvionAI API.

### NDVIResult Class

#### Properties
- `image_id`: Unique identifier for the processed image
- `visualization_b64`: Base64-encoded NDVI visualization
- `has_ground_truth`: Whether ground truth data is available

#### `save_image(filepath, format="PNG") -> str`
Save the NDVI visualization to a file.

## Getting Help

- 📧 Email: support@evionai.com
- 🌐 Documentation: [https://docs.evionai.com](https://docs.evionai.com)
- 🐛 Issues: [https://github.com/evionai/evion-ndvi-sdk/issues](https://github.com/evionai/evion-ndvi-sdk/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

---

**Made with 🌱 by the EvionAI Team** 
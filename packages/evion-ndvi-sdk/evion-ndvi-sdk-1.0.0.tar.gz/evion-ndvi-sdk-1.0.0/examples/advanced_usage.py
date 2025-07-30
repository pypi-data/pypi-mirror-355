#!/usr/bin/env python3
"""
Advanced usage example for EvionAI NDVI SDK

This example demonstrates:
1. Batch processing multiple images
2. Error handling and retries
3. Custom result handling
4. Different input methods
"""

import os
from pathlib import Path
import time
from evion_ndvi_sdk import EvionNDVI, EvionNDVIError, RateLimitError

def process_multiple_images(client, image_directory, output_directory):
    """Process all images in a directory"""
    image_dir = Path(image_directory)
    output_dir = Path(output_directory)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Supported image extensions
    supported_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}
    
    # Find all image files
    image_files = [
        f for f in image_dir.glob('*') 
        if f.suffix.lower() in supported_extensions
    ]
    
    if not image_files:
        print(f"No supported image files found in {image_directory}")
        return
    
    print(f"Found {len(image_files)} images to process")
    
    results = []
    failed_images = []
    
    for i, image_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Processing: {image_path.name}")
        
        try:
            # Process with retry logic for rate limits
            result = process_with_retry(client, image_path, output_dir)
            results.append((image_path.name, result))
            print(f"✅ Success: {result.image_id}")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            failed_images.append((image_path.name, str(e)))
    
    # Print summary
    print("\n" + "="*50)
    print("BATCH PROCESSING SUMMARY")
    print("="*50)
    print(f"Total images: {len(image_files)}")
    print(f"Successful: {len(results)}")
    print(f"Failed: {len(failed_images)}")
    
    if failed_images:
        print("\nFailed images:")
        for filename, error in failed_images:
            print(f"  - {filename}: {error}")

def process_with_retry(client, image_path, output_dir, max_retries=3):
    """Process an image with retry logic for rate limits"""
    for attempt in range(max_retries):
        try:
            return client.predict_from_file(
                image_path=image_path,
                auto_download=True,
                download_dir=output_dir
            )
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise
        except Exception:
            raise

def demonstrate_different_inputs(client):
    """Demonstrate different ways to provide input to the SDK"""
    print("\n" + "="*50)
    print("DEMONSTRATING DIFFERENT INPUT METHODS")
    print("="*50)
    
    # Method 1: Random image
    print("\n1. Using random sample image:")
    try:
        result = client.predict_random(download_dir="./random_samples")
        print(f"✅ Random image processed: {result.image_id}")
    except Exception as e:
        print(f"❌ Random image failed: {e}")
    
    # Method 2: From bytes (if you have an image file)
    print("\n2. Using image bytes:")
    sample_image = Path("crop_image.jpg")  # Change to an actual image file
    if sample_image.exists():
        try:
            with open(sample_image, 'rb') as f:
                image_bytes = f.read()
            
            result = client.predict_from_bytes(
                image_data=image_bytes,
                filename=sample_image.stem,
                download_dir="./bytes_samples"
            )
            print(f"✅ Bytes image processed: {result.image_id}")
        except Exception as e:
            print(f"❌ Bytes image failed: {e}")
    else:
        print("Skipping bytes example - no sample image found")

def main():
    # Configuration
    API_KEY = "your_api_key_here"  # Replace with your actual API key
    IMAGE_DIRECTORY = "./input_images"  # Directory containing crop images
    OUTPUT_DIRECTORY = "./batch_results"  # Where to save results
    
    # Initialize client
    client = EvionNDVI(api_key=API_KEY)
    
    # Test connection
    print("🔍 Testing connection...")
    if not client.test_connection():
        print("❌ Connection failed. Exiting.")
        return
    print("✅ Connection successful!")
    
    # Demonstrate different input methods
    demonstrate_different_inputs(client)
    
    # Check if input directory exists
    if not Path(IMAGE_DIRECTORY).exists():
        print(f"\n📁 Creating example directory: {IMAGE_DIRECTORY}")
        print("   Add your crop images to this directory and run again.")
        Path(IMAGE_DIRECTORY).mkdir(parents=True, exist_ok=True)
        return
    
    # Process multiple images
    process_multiple_images(client, IMAGE_DIRECTORY, OUTPUT_DIRECTORY)

if __name__ == "__main__":
    main() 
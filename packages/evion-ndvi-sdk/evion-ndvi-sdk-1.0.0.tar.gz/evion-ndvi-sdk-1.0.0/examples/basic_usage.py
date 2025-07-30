#!/usr/bin/env python3
"""
Basic usage example for EvionAI NDVI SDK

This example shows how to:
1. Initialize the EvionNDVI client with your API key
2. Upload a crop image and get NDVI prediction
3. Automatically download the result

Prerequisites:
1. Sign up at https://platform.evionai.com
2. Create an API key in your dashboard
3. Replace "your_api_key_here" with your actual API key
4. Have a crop image file ready
"""

from evion_ndvi_sdk import EvionNDVI, EvionNDVIError

def main():
    # Step 1: Initialize the client with your API key
    # TODO: Replace with your actual API key from https://platform.evionai.com
    API_KEY = "your_api_key_here"
    
    client = EvionNDVI(api_key=API_KEY)
    
    # Step 2: Test connection (optional but recommended)
    print("🔍 Testing connection to EvionAI...")
    if not client.test_connection():
        print("❌ Connection failed. Please check your API key and network.")
        return
    
    print("✅ Connection successful!")
    
    try:
        # Step 3: Generate NDVI prediction from your crop image
        # Replace "crop_image.jpg" with the path to your actual image
        image_path = "crop_image.jpg"  # Change this to your image file
        
        print(f"📸 Processing image: {image_path}")
        
        result = client.predict_from_file(
            image_path=image_path,
            auto_download=True,  # Automatically save the result
            download_dir="./ndvi_results"  # Save to this directory
        )
        
        # Step 4: View results
        print("🎉 NDVI prediction completed successfully!")
        print(f"   Image ID: {result.image_id}")
        print(f"   Ground truth available: {result.has_ground_truth}")
        print(f"   Result saved to: ./ndvi_results/{image_path.split('/')[-1].split('.')[0]}_ndvi.png")
        
        # You can also manually save to a specific location
        custom_path = result.save_image("my_custom_ndvi_result.png")
        print(f"   Also saved to: {custom_path}")
        
    except FileNotFoundError:
        print(f"❌ Error: Image file '{image_path}' not found.")
        print("   Please make sure the image file exists and update the path in this script.")
    except EvionNDVIError as e:
        print(f"❌ EvionAI Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 
"""
Command-line interface for EvionAI NDVI SDK
"""

import argparse
import sys
from pathlib import Path

from .client import EvionNDVI
from .exceptions import EvionNDVIError


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="EvionAI NDVI SDK - Generate NDVI predictions from crop images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  evion-ndvi --api-key YOUR_API_KEY --image crop.jpg
  evion-ndvi --api-key YOUR_API_KEY --random
  evion-ndvi --api-key YOUR_API_KEY --image crop.tif --output-dir /path/to/results
        """
    )
    
    parser.add_argument(
        "--api-key", 
        required=True,
        help="Your EvionAI API key (get one from https://platform.evionai.com)"
    )
    
    parser.add_argument(
        "--image", 
        type=Path,
        help="Path to crop image file (.tif, .tiff, .jpg, .png)"
    )
    
    parser.add_argument(
        "--random", 
        action="store_true",
        help="Generate prediction using a random sample image"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=Path,
        default=".",
        help="Directory to save NDVI result images (default: current directory)"
    )
    
    parser.add_argument(
        "--base-url", 
        default="http://localhost:8000",
        help="Base URL for EvionAI API (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--no-download", 
        action="store_true",
        help="Don't automatically download result images"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Test connection to EvionAI API"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.test and not args.random and not args.image:
        parser.error("Either --image, --random, or --test must be specified")
    
    if args.image and args.random:
        parser.error("Cannot specify both --image and --random")
    
    try:
        # Initialize client
        client = EvionNDVI(api_key=args.api_key, base_url=args.base_url)
        
        if args.test:
            print("🔍 Testing connection to EvionAI API...")
            if client.test_connection():
                print("✅ Connection successful! Your API key is working.")
                return 0
            else:
                print("❌ Connection failed. Please check your API key and network connection.")
                return 1
        
        auto_download = not args.no_download
        
        if args.random:
            print("🎲 Generating NDVI prediction with random image...")
            result = client.predict_random(
                auto_download=auto_download,
                download_dir=args.output_dir
            )
            print(f"✅ Prediction completed: {result}")
            
        elif args.image:
            if not args.image.exists():
                print(f"❌ Error: Image file not found: {args.image}")
                return 1
                
            print(f"📸 Generating NDVI prediction for: {args.image}")
            result = client.predict_from_file(
                image_path=args.image,
                auto_download=auto_download,
                download_dir=args.output_dir
            )
            print(f"✅ Prediction completed: {result}")
        
        return 0
        
    except EvionNDVIError as e:
        print(f"❌ EvionAI Error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
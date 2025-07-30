"""
Main client class for EvionAI NDVI SDK
"""

import os
import base64
import requests
from pathlib import Path
from typing import Optional, Union, Dict, Any
from PIL import Image
import io

from .exceptions import (
    AuthenticationError,
    APIError,
    RateLimitError,
    InvalidImageError,
    NetworkError,
)


class NDVIResult:
    """Container class for NDVI prediction results"""
    
    def __init__(self, image_id: str, visualization_b64: str, has_ground_truth: bool = False):
        self.image_id = image_id
        self.visualization_b64 = visualization_b64
        self.has_ground_truth = has_ground_truth
    
    def save_image(self, filepath: Union[str, Path], format: str = "PNG") -> str:
        """
        Save the NDVI visualization image to a file
        
        Args:
            filepath: Path where to save the image
            format: Image format (PNG, JPEG, etc.)
            
        Returns:
            str: Absolute path of the saved file
        """
        filepath = Path(filepath)
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Decode base64 image
        image_data = base64.b64decode(self.visualization_b64)
        image = Image.open(io.BytesIO(image_data))
        
        # Save image
        image.save(filepath, format=format)
        
        return str(filepath.absolute())
    
    def __repr__(self):
        return f"NDVIResult(image_id='{self.image_id}', has_ground_truth={self.has_ground_truth})"


class EvionNDVI:
    """
    EvionAI NDVI SDK Client
    
    A simple client for uploading crop images and generating synthetic NDVI predictions.
    """
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        """
        Initialize EvionNDVI client
        
        Args:
            api_key: Your EvionAI API key (get one from https://platform.evionai.com)
            base_url: Base URL for the EvionAI API (default: http://localhost:8000)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'User-Agent': 'EvionNDVI-SDK/1.0.0'
        })
    
    def predict_from_file(self, image_path: Union[str, Path], 
                         auto_download: bool = True, 
                         download_dir: Optional[Union[str, Path]] = None) -> NDVIResult:
        """
        Generate NDVI prediction from an image file
        
        Args:
            image_path: Path to the crop image file (.tif, .tiff, .jpg, .png)
            auto_download: Whether to automatically download the result image
            download_dir: Directory to save the result (default: same as input image)
            
        Returns:
            NDVIResult: Object containing the prediction results
            
        Raises:
            InvalidImageError: If image file is invalid or unsupported
            AuthenticationError: If API key is invalid
            APIError: If API request fails
            NetworkError: If network connection fails
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise InvalidImageError(f"Image file not found: {image_path}")
        
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (image_path.name, f, 'application/octet-stream')}
                result = self._make_prediction_request(files)
                
            if auto_download:
                if download_dir is None:
                    download_dir = image_path.parent
                
                download_path = Path(download_dir) / f"{image_path.stem}_ndvi.png"
                result.save_image(download_path)
                print(f"✅ NDVI result saved to: {download_path}")
                
            return result
            
        except FileNotFoundError:
            raise InvalidImageError(f"Image file not found: {image_path}")
        except IOError as e:
            raise InvalidImageError(f"Error reading image file: {e}")
    
    def predict_from_bytes(self, image_data: bytes, filename: str = "image", 
                          auto_download: bool = True, 
                          download_dir: Union[str, Path] = ".") -> NDVIResult:
        """
        Generate NDVI prediction from image bytes
        
        Args:
            image_data: Raw image data as bytes
            filename: Name for the image (used in API request)
            auto_download: Whether to automatically download the result image
            download_dir: Directory to save the result (default: current directory)
            
        Returns:
            NDVIResult: Object containing the prediction results
        """
        try:
            files = {'file': (filename, io.BytesIO(image_data), 'application/octet-stream')}
            result = self._make_prediction_request(files)
            
            if auto_download:
                download_path = Path(download_dir) / f"{filename}_ndvi.png"
                result.save_image(download_path)
                print(f"✅ NDVI result saved to: {download_path}")
                
            return result
            
        except Exception as e:
            raise InvalidImageError(f"Error processing image data: {e}")
    
    def predict_random(self, auto_download: bool = True, 
                      download_dir: Union[str, Path] = ".") -> NDVIResult:
        """
        Generate NDVI prediction using a random sample image
        
        Args:
            auto_download: Whether to automatically download the result image
            download_dir: Directory to save the result (default: current directory)
            
        Returns:
            NDVIResult: Object containing the prediction results
        """
        try:
            response = self.session.get(f"{self.base_url}/api/model/ndvi/random")
            self._handle_response(response)
            
            data = response.json()
            result = NDVIResult(
                image_id=data['image_id'],
                visualization_b64=data['visualization'],
                has_ground_truth=data.get('has_ground_truth', False)
            )
            
            if auto_download:
                download_path = Path(download_dir) / f"random_{data['image_id']}_ndvi.png"
                result.save_image(download_path)
                print(f"✅ NDVI result saved to: {download_path}")
                
            return result
            
        except requests.RequestException as e:
            raise NetworkError(f"Network error: {e}")
    
    def _make_prediction_request(self, files: Dict[str, Any]) -> NDVIResult:
        """Make a prediction request to the API"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/model/ndvi/predict",
                files=files
            )
            
            self._handle_response(response)
            
            data = response.json()
            return NDVIResult(
                image_id=data['image_id'],
                visualization_b64=data['visualization'],
                has_ground_truth=data.get('has_ground_truth', False)
            )
            
        except requests.RequestException as e:
            raise NetworkError(f"Network error: {e}")
    
    def _handle_response(self, response: requests.Response):
        """Handle API response and raise appropriate exceptions"""
        if response.status_code == 200:
            return
        
        try:
            error_data = response.json()
            error_message = error_data.get('detail', 'Unknown error')
        except ValueError:
            error_message = response.text or f"HTTP {response.status_code}"
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key. Please check your credentials.")
        elif response.status_code == 429:
            raise RateLimitError("API rate limit exceeded. Please try again later or upgrade your plan.")
        elif response.status_code >= 500:
            raise APIError(f"Server error: {error_message}", response.status_code, error_data)
        else:
            raise APIError(f"API error: {error_message}", response.status_code, error_data)
    
    def test_connection(self) -> bool:
        """
        Test the connection to EvionAI API
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/api/model/ndvi/random")
            return response.status_code == 200
        except:
            return False 
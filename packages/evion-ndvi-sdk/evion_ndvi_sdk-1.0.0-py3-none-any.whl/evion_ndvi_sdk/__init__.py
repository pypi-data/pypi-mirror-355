"""
EvionAI NDVI SDK - Python library for crop image NDVI prediction

This SDK provides a simple interface to upload crop images and generate
synthetic NDVI predictions using EvionAI's machine learning models.
"""

from .client import EvionNDVI
from .exceptions import EvionNDVIError, AuthenticationError, APIError, RateLimitError

__version__ = "1.0.0"
__author__ = "EvionAI"
__email__ = "support@evionai.com"

__all__ = [
    "EvionNDVI",
    "EvionNDVIError",
    "AuthenticationError", 
    "APIError",
    "RateLimitError",
] 
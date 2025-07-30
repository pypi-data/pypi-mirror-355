"""
Custom exceptions for EvionAI NDVI SDK
"""


class EvionNDVIError(Exception):
    """Base exception class for EvionAI NDVI SDK"""
    pass


class AuthenticationError(EvionNDVIError):
    """Raised when API key authentication fails"""
    pass


class APIError(EvionNDVIError):
    """Raised when the API returns an error response"""
    
    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimitError(EvionNDVIError):
    """Raised when API rate limit is exceeded"""
    pass


class InvalidImageError(EvionNDVIError):
    """Raised when provided image is invalid or unsupported"""
    pass


class NetworkError(EvionNDVIError):
    """Raised when network connection fails"""
    pass 
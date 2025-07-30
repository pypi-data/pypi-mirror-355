"""OpenAI Vision Cost Calculator.

A Python library for calculating the cost of image inputs to OpenAI vision models.
"""

__version__ = "1.0.0"
__author__ = "Alex Ferrari"
__email__ = "alex@thealexferrari.com"

from .calculator import calculate_image_cost, calculate_tokens_only, estimate_cost_range
from .models import get_supported_models, is_model_supported
from .exceptions import (
    OpenAIVisionCostError,
    UnsupportedModelError,
    InvalidImageDimensionsError,
    InvalidPricingError,
    InvalidDetailLevelError,
)

__all__ = [
    # Main functions
    "calculate_image_cost",
    "calculate_tokens_only", 
    "estimate_cost_range",
    
    # Model utilities
    "get_supported_models",
    "is_model_supported",
    
    # Exceptions
    "OpenAIVisionCostError",
    "UnsupportedModelError",
    "InvalidImageDimensionsError",
    "InvalidPricingError",
    "InvalidDetailLevelError",
]
"""Core cost calculation logic for OpenAI vision models."""

import math
from typing import Dict, Union, Tuple

from .models import get_model_config, ModelFamily
from .exceptions import (
    InvalidImageDimensionsError,
    InvalidPricingError,
    InvalidDetailLevelError,
    UnsupportedModelError,
)


def _validate_inputs(
    width: int, height: int, model: str, input_price_per_million: float, detail: str
) -> None:
    """Validate input parameters.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        model: Model name
        input_price_per_million: Price per million tokens
        detail: Detail level ('high' or 'low')
        
    Raises:
        InvalidImageDimensionsError: If dimensions are invalid
        InvalidPricingError: If pricing is invalid
        InvalidDetailLevelError: If detail level is invalid
        UnsupportedModelError: If model is not supported
    """
    if width <= 0 or height <= 0:
        raise InvalidImageDimensionsError(width, height)
    
    if input_price_per_million <= 0:
        raise InvalidPricingError(input_price_per_million)
    
    if detail not in ("high", "low"):
        raise InvalidDetailLevelError(detail)
    
    # This will raise UnsupportedModelError if model is not supported
    get_model_config(model)


def _calculate_patch_based_tokens(
    width: int, height: int, patch_size: int, max_patches: int
) -> int:
    """Calculate tokens for patch-based models (GPT-4.1-mini/nano, o4-mini).
    
    Based on OpenAI documentation:
    - Calculate number of 32px x 32px patches needed to cover the image
    - If patches exceed 1536, scale down the image to fit within 1536 patches
    - Return the number of patches (capped at 1536)
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        patch_size: Size of each patch (32px for these models)
        max_patches: Maximum number of patches (1536)
        
    Returns:
        Number of image tokens (patches)
    """
    # Calculate initial patches needed
    width_patches = math.ceil(width / patch_size)
    height_patches = math.ceil(height / patch_size)
    total_patches = width_patches * height_patches
    
    if total_patches <= max_patches:
        return total_patches
    
    # Need to scale down the image
    # Calculate shrink factor to fit within max_patches
    shrink_factor = math.sqrt(max_patches * patch_size**2 / (width * height))
    
    # Apply shrink factor
    new_width = width * shrink_factor
    new_height = height * shrink_factor
    
    # Calculate patches for scaled image
    new_width_patches = new_width / patch_size
    new_height_patches = new_height / patch_size
    
    # Ensure we fit in whole number of patches (scale down further if needed)
    width_patches_int = int(new_width_patches)
    if width_patches_int == 0:
        width_patches_int = 1
        
    # Adjust height proportionally to maintain aspect ratio within patch constraint
    additional_shrink = width_patches_int / new_width_patches
    final_height_patches = int(new_height_patches * additional_shrink)
    if final_height_patches == 0:
        final_height_patches = 1
    
    return min(width_patches_int * final_height_patches, max_patches)


def _calculate_tile_based_tokens(
    width: int, height: int, config, detail: str
) -> int:
    """Calculate tokens for tile-based models.
    
    Based on OpenAI documentation and observed behavior:
    - Scale to fit in a 2048px x 2048px square, maintaining aspect ratio
    - Scale so that the shortest side is 768px long (512px for gpt-image-1)
      BUT only if the image is larger than the target
    - Count number of 512px squares, each costs tile_tokens
    - Add base_tokens to the total
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        config: Model configuration
        detail: Detail level ('high' or 'low')
        
    Returns:
        Number of tokens
    """
    if detail == "low":
        return config.base_tokens
    
    # Step 1: Scale to fit in max_dimension x max_dimension square
    max_dim = max(width, height)
    if max_dim > config.max_dimension:
        scale_factor = config.max_dimension / max_dim
        width = int(width * scale_factor)
        height = int(height * scale_factor)
    
    # Step 2: Scale so shortest side is target length
    # BUT only scale UP if the shortest side is already larger than target
    min_side = min(width, height)
    if min_side > config.shortest_side_target:
        scale_factor = config.shortest_side_target / min_side
        width = int(width * scale_factor)
        height = int(height * scale_factor)
    
    # Step 3: Count 512px tiles
    width_tiles = math.ceil(width / config.patch_size)
    height_tiles = math.ceil(height / config.patch_size)
    total_tiles = width_tiles * height_tiles
    
    # Step 4: Calculate total tokens
    return config.base_tokens + (total_tiles * config.tile_tokens)


def calculate_tokens_only(
    width: int, height: int, model: str, detail: str = "high"
) -> Dict[str, Union[int, float]]:
    """Calculate only token counts for an image.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        model: Model name (e.g., 'gpt-4o', 'gpt-4.1-mini')
        detail: Detail level, 'high' or 'low' (default: 'high')
        
    Returns:
        Dictionary with token information:
        - 'image_tokens': Raw image tokens calculated from dimensions
        - 'text_tokens': Final tokens used for billing (after multiplier if applicable)
        
    Raises:
        InvalidImageDimensionsError: If width or height is <= 0
        InvalidDetailLevelError: If detail is not 'high' or 'low'
        UnsupportedModelError: If model is not supported
    """
    # Validate inputs (skip pricing validation)
    if width <= 0 or height <= 0:
        raise InvalidImageDimensionsError(width, height)
    
    if detail not in ("high", "low"):
        raise InvalidDetailLevelError(detail)
    
    config = get_model_config(model)
    
    if config.family == ModelFamily.PATCH_BASED:
        # Calculate image tokens from patches
        image_tokens = _calculate_patch_based_tokens(
            width, height, config.patch_size, config.max_patches
        )
        # Apply multiplier to get text tokens for billing
        text_tokens = int(image_tokens * config.multiplier)
        
    elif config.family in (ModelFamily.TILE_BASED, ModelFamily.IMAGE_TOKENS):
        # For these models, the calculation directly gives text/image tokens
        tokens = _calculate_tile_based_tokens(width, height, config, detail)
        image_tokens = tokens
        text_tokens = tokens
    
    return {
        "image_tokens": image_tokens,
        "text_tokens": text_tokens,
    }


def calculate_image_cost(
    width: int,
    height: int,
    model: str,
    input_price_per_million: float,
    detail: str = "high",
) -> Dict[str, Union[int, float]]:
    """Calculate the cost of processing an image with OpenAI vision models.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        model: Model name (e.g., 'gpt-4o', 'gpt-4.1-mini')
        input_price_per_million: Price per million tokens in USD
        detail: Detail level, 'high' or 'low' (default: 'high')
        
    Returns:
        Dictionary with cost information:
        - 'image_tokens': Raw image tokens calculated from dimensions
        - 'text_tokens': Final tokens used for billing (after multiplier if applicable)
        - 'total_cost_usd': Total cost in USD
        
    Raises:
        InvalidImageDimensionsError: If width or height is <= 0
        InvalidPricingError: If input_price_per_million is <= 0
        InvalidDetailLevelError: If detail is not 'high' or 'low'
        UnsupportedModelError: If model is not supported
        
    Example:
        >>> calculate_image_cost(1024, 1024, "gpt-4o", 2.50)
        {'image_tokens': 765, 'text_tokens': 765, 'total_cost_usd': 0.0019125}
    """
    _validate_inputs(width, height, model, input_price_per_million, detail)
    
    # Get token counts
    token_info = calculate_tokens_only(width, height, model, detail)
    
    # Calculate cost based on text tokens (what's actually billed)
    cost_usd = token_info["text_tokens"] * (input_price_per_million / 1_000_000)
    
    return {
        "image_tokens": token_info["image_tokens"],
        "text_tokens": token_info["text_tokens"],
        "total_cost_usd": cost_usd,
    }


def estimate_cost_range(
    width: int, height: int, model: str, input_price_per_million: float
) -> Dict[str, Dict[str, Union[int, float]]]:
    """Estimate cost range for both high and low detail levels.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        model: Model name
        input_price_per_million: Price per million tokens in USD
        
    Returns:
        Dictionary with 'high' and 'low' detail cost estimates
        
    Example:
        >>> estimate_cost_range(1024, 1024, "gpt-4o", 2.50)
        {
            'high': {'image_tokens': 765, 'text_tokens': 765, 'total_cost_usd': 0.0019125},
            'low': {'image_tokens': 85, 'text_tokens': 85, 'total_cost_usd': 0.0002125}
        }
    """
    return {
        "high": calculate_image_cost(width, height, model, input_price_per_million, "high"),
        "low": calculate_image_cost(width, height, model, input_price_per_million, "low"),
    }
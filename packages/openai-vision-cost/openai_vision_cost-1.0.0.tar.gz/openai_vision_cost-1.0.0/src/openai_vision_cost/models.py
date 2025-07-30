"""Model configurations and parameters for OpenAI vision models."""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from .exceptions import UnsupportedModelError


class ModelFamily(Enum):
    """Model families with different cost calculation methods."""
    PATCH_BASED = "patch_based"  # GPT-4.1-mini/nano, o4-mini (32px patches)
    TILE_BASED = "tile_based"    # GPT-4o/4.1/4o-mini/CUA/o-series (512px tiles)
    IMAGE_TOKENS = "image_tokens"  # GPT Image 1 (separate image token pricing)


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    family: ModelFamily
    base_tokens: int = 0
    tile_tokens: int = 0
    multiplier: float = 1.0
    shortest_side_target: int = 768
    max_dimension: int = 2048
    patch_size: int = 512
    max_patches: int = 1536


# Model configurations based on OpenAI documentation
MODEL_CONFIGS: Dict[str, ModelConfig] = {
    # GPT-4.1-mini/nano, o4-mini family (32px patch-based)
    "gpt-4.1-mini": ModelConfig(
        family=ModelFamily.PATCH_BASED,
        multiplier=1.62,
        patch_size=32,
        max_patches=1536
    ),
    "gpt-4.1-nano": ModelConfig(
        family=ModelFamily.PATCH_BASED,
        multiplier=2.46,
        patch_size=32,
        max_patches=1536
    ),
    "o4-mini": ModelConfig(
        family=ModelFamily.PATCH_BASED,
        multiplier=1.72,
        patch_size=32,
        max_patches=1536
    ),
    
    # GPT-4o, GPT-4.1, GPT-4o-mini, CUA, and o-series family (512px tile-based)
    "gpt-4o": ModelConfig(
        family=ModelFamily.TILE_BASED,
        base_tokens=85,
        tile_tokens=170,
        shortest_side_target=768,
        max_dimension=2048,
        patch_size=512
    ),
    "gpt-4.1": ModelConfig(
        family=ModelFamily.TILE_BASED,
        base_tokens=85,
        tile_tokens=170,
        shortest_side_target=768,
        max_dimension=2048,
        patch_size=512
    ),
    "gpt-4.5": ModelConfig(
        family=ModelFamily.TILE_BASED,
        base_tokens=85,
        tile_tokens=170,
        shortest_side_target=768,
        max_dimension=2048,
        patch_size=512
    ),
    "gpt-4o-mini": ModelConfig(
        family=ModelFamily.TILE_BASED,
        base_tokens=2833,
        tile_tokens=5667,
        shortest_side_target=768,
        max_dimension=2048,
        patch_size=512
    ),
    "o1": ModelConfig(
        family=ModelFamily.TILE_BASED,
        base_tokens=75,
        tile_tokens=150,
        shortest_side_target=768,
        max_dimension=2048,
        patch_size=512
    ),
    "o1-pro": ModelConfig(
        family=ModelFamily.TILE_BASED,
        base_tokens=75,
        tile_tokens=150,
        shortest_side_target=768,
        max_dimension=2048,
        patch_size=512
    ),
    "o3": ModelConfig(
        family=ModelFamily.TILE_BASED,
        base_tokens=75,
        tile_tokens=150,
        shortest_side_target=768,
        max_dimension=2048,
        patch_size=512
    ),
    "o3-pro": ModelConfig(
        family=ModelFamily.TILE_BASED,
        base_tokens=75,
        tile_tokens=150,
        shortest_side_target=768,
        max_dimension=2048,
        patch_size=512
    ),
    "o3-mini": ModelConfig(
        family=ModelFamily.TILE_BASED,
        base_tokens=75,
        tile_tokens=150,
        shortest_side_target=768,
        max_dimension=2048,
        patch_size=512
    ),
    "o1-mini": ModelConfig(
        family=ModelFamily.TILE_BASED,
        base_tokens=75,
        tile_tokens=150,
        shortest_side_target=768,
        max_dimension=2048,
        patch_size=512
    ),
    "computer-use-preview": ModelConfig(
        family=ModelFamily.TILE_BASED,
        base_tokens=65,
        tile_tokens=129,
        shortest_side_target=768,
        max_dimension=2048,
        patch_size=512
    ),
    
    # GPT Image 1 (special case with 512px shortest side)
    "gpt-image-1": ModelConfig(
        family=ModelFamily.IMAGE_TOKENS,
        base_tokens=65,
        tile_tokens=129,
        shortest_side_target=512,
        max_dimension=2048,
        patch_size=512
    ),
}

# Model name aliases and variations
MODEL_ALIASES: Dict[str, str] = {
    # Common variations
    "gpt-4o-2024-08-06": "gpt-4o",
    "gpt-4o-2024-05-13": "gpt-4o",
    "gpt-4o-mini-2024-07-18": "gpt-4o-mini",
    "gpt-4.1-2024-12-17": "gpt-4.1",
    "gpt-4.1-mini-2024-12-17": "gpt-4.1-mini",
    "gpt-4.1-nano-2024-12-17": "gpt-4.1-nano",
    "o1-2024-12-17": "o1",
    "o1-pro-2024-12-17": "o1-pro",
    "o3-2024-12-17": "o3",
    "o3-pro-2024-12-17": "o3-pro",
    "o3-mini-2024-12-17": "o3-mini",
    "o1-mini-2024-09-12": "o1-mini",
    "o4-mini-2024-12-17": "o4-mini",
    
    # Preview and variant models
    "gpt-4o-audio-preview": "gpt-4o",
    "gpt-4o-realtime-preview": "gpt-4o",
    "gpt-4o-mini-audio-preview": "gpt-4o-mini",
    "gpt-4o-mini-realtime-preview": "gpt-4o-mini",
    "gpt-4o-mini-search-preview": "gpt-4o-mini",
    "gpt-4o-search-preview": "gpt-4o",
    "gpt-4.5-preview": "gpt-4.5",
}


def get_model_config(model_name: str) -> ModelConfig:
    """Get model configuration for a given model name.
    
    Args:
        model_name: The model name (e.g., 'gpt-4o', 'gpt-4.1-mini')
        
    Returns:
        ModelConfig object for the model
        
    Raises:
        UnsupportedModelError: If model is not supported
    """
    # Normalize model name
    normalized_name = MODEL_ALIASES.get(model_name, model_name)
    
    if normalized_name not in MODEL_CONFIGS:
        raise UnsupportedModelError(model_name)
    
    return MODEL_CONFIGS[normalized_name]


def get_supported_models() -> List[str]:
    """Get list of all supported model names.
    
    Returns:
        List of supported model names
    """
    base_models = list(MODEL_CONFIGS.keys())
    alias_models = list(MODEL_ALIASES.keys())
    return sorted(base_models + alias_models)


def is_model_supported(model_name: str) -> bool:
    """Check if a model is supported.
    
    Args:
        model_name: The model name to check
        
    Returns:
        True if model is supported, False otherwise
    """
    normalized_name = MODEL_ALIASES.get(model_name, model_name)
    return normalized_name in MODEL_CONFIGS
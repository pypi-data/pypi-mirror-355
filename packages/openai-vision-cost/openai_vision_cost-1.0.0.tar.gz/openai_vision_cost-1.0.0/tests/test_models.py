"""Tests for the models module."""

import pytest
from openai_vision_cost.models import (
    get_model_config,
    get_supported_models,
    is_model_supported,
    ModelFamily,
    MODEL_CONFIGS,
    MODEL_ALIASES,
)
from openai_vision_cost.exceptions import UnsupportedModelError


class TestModelConfig:
    """Tests for model configuration retrieval."""

    def test_get_model_config_basic(self):
        """Test getting config for basic model names."""
        config = get_model_config("gpt-4o")
        assert config.family == ModelFamily.TILE_BASED
        assert config.base_tokens == 85
        assert config.tile_tokens == 170

    def test_get_model_config_with_alias(self):
        """Test getting config with model alias."""
        config1 = get_model_config("gpt-4o")
        config2 = get_model_config("gpt-4o-2024-08-06")
        
        assert config1.family == config2.family
        assert config1.base_tokens == config2.base_tokens
        assert config1.tile_tokens == config2.tile_tokens

    def test_get_model_config_unsupported(self):
        """Test getting config for unsupported model."""
        with pytest.raises(UnsupportedModelError) as exc_info:
            get_model_config("unsupported-model")
        
        assert "unsupported-model" in str(exc_info.value)

    def test_patch_based_models(self):
        """Test patch-based model configurations."""
        for model_name in ["gpt-4.1-mini", "gpt-4.1-nano", "o4-mini"]:
            config = get_model_config(model_name)
            assert config.family == ModelFamily.PATCH_BASED
            assert config.patch_size == 32
            assert config.max_patches == 1536
            assert config.multiplier > 1.0

    def test_tile_based_models(self):
        """Test tile-based model configurations."""
        tile_models = [
            "gpt-4o", "gpt-4.1", "gpt-4.5", "gpt-4o-mini", 
            "o1", "o1-pro", "o3", "o3-pro", "o3-mini", "o1-mini",
            "computer-use-preview"
        ]
        
        for model_name in tile_models:
            config = get_model_config(model_name)
            assert config.family == ModelFamily.TILE_BASED
            assert config.base_tokens > 0
            assert config.tile_tokens > 0
            assert config.shortest_side_target == 768
            assert config.max_dimension == 2048
            assert config.patch_size == 512

    def test_image_tokens_model(self):
        """Test image tokens model configuration."""
        config = get_model_config("gpt-image-1")
        assert config.family == ModelFamily.IMAGE_TOKENS
        assert config.base_tokens == 65
        assert config.tile_tokens == 129
        assert config.shortest_side_target == 512  # Different from others

    def test_multiplier_values(self):
        """Test specific multiplier values for patch-based models."""
        assert get_model_config("gpt-4.1-mini").multiplier == 1.62
        assert get_model_config("gpt-4.1-nano").multiplier == 2.46
        assert get_model_config("o4-mini").multiplier == 1.72

    def test_base_and_tile_tokens(self):
        """Test specific base and tile token values."""
        # GPT-4o family
        gpt4o_config = get_model_config("gpt-4o")
        assert gpt4o_config.base_tokens == 85
        assert gpt4o_config.tile_tokens == 170
        
        # GPT-4o-mini has different values
        gpt4o_mini_config = get_model_config("gpt-4o-mini")
        assert gpt4o_mini_config.base_tokens == 2833
        assert gpt4o_mini_config.tile_tokens == 5667
        
        # o1 family
        o1_config = get_model_config("o1")
        assert o1_config.base_tokens == 75
        assert o1_config.tile_tokens == 150


class TestSupportedModels:
    """Tests for supported models functionality."""

    def test_get_supported_models(self):
        """Test getting list of supported models."""
        models = get_supported_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert "gpt-4o" in models
        assert "gpt-4.1-mini" in models
        assert "gpt-4o-2024-08-06" in models  # Alias
        
        # Should be sorted
        assert models == sorted(models)

    def test_is_model_supported(self):
        """Test model support checking."""
        # Base models
        assert is_model_supported("gpt-4o")
        assert is_model_supported("gpt-4.1-mini")
        assert is_model_supported("gpt-image-1")
        
        # Aliases
        assert is_model_supported("gpt-4o-2024-08-06")
        assert is_model_supported("gpt-4o-audio-preview")
        
        # Non-existent models
        assert not is_model_supported("unsupported-model")
        assert not is_model_supported("gpt-3.5-turbo")

    def test_all_base_models_supported(self):
        """Test that all base models are supported."""
        for model_name in MODEL_CONFIGS.keys():
            assert is_model_supported(model_name)

    def test_all_aliases_supported(self):
        """Test that all aliases are supported."""
        for alias in MODEL_ALIASES.keys():
            assert is_model_supported(alias)

    def test_supported_models_includes_all(self):
        """Test that get_supported_models includes all models."""
        supported = get_supported_models()
        
        # Should include all base models
        for model_name in MODEL_CONFIGS.keys():
            assert model_name in supported
        
        # Should include all aliases
        for alias in MODEL_ALIASES.keys():
            assert alias in supported


class TestModelAliases:
    """Tests for model aliases functionality."""

    def test_date_suffixed_aliases(self):
        """Test date-suffixed model aliases."""
        date_aliases = [
            ("gpt-4o-2024-08-06", "gpt-4o"),
            ("gpt-4o-mini-2024-07-18", "gpt-4o-mini"),
            ("gpt-4.1-2024-12-17", "gpt-4.1"),
            ("o1-2024-12-17", "o1"),
        ]
        
        for alias, base in date_aliases:
            assert MODEL_ALIASES[alias] == base

    def test_preview_aliases(self):
        """Test preview model aliases."""
        preview_aliases = [
            ("gpt-4o-audio-preview", "gpt-4o"),
            ("gpt-4o-realtime-preview", "gpt-4o"),
            ("gpt-4o-mini-audio-preview", "gpt-4o-mini"),
            ("gpt-4.5-preview", "gpt-4.5"),
        ]
        
        for alias, base in preview_aliases:
            assert MODEL_ALIASES[alias] == base

    def test_alias_resolution(self):
        """Test that aliases resolve to correct base models."""
        # Test that alias points to existing base model
        for alias, base_model in MODEL_ALIASES.items():
            assert base_model in MODEL_CONFIGS

    def test_no_circular_aliases(self):
        """Test that there are no circular alias references."""
        for alias, target in MODEL_ALIASES.items():
            # Target should not be another alias
            assert target not in MODEL_ALIASES


class TestModelFamilies:
    """Tests for model family classifications."""

    def test_patch_based_family(self):
        """Test patch-based family models."""
        patch_models = ["gpt-4.1-mini", "gpt-4.1-nano", "o4-mini"]
        
        for model in patch_models:
            config = get_model_config(model)
            assert config.family == ModelFamily.PATCH_BASED

    def test_tile_based_family(self):
        """Test tile-based family models."""
        tile_models = [
            "gpt-4o", "gpt-4.1", "gpt-4.5", "gpt-4o-mini",
            "o1", "o1-pro", "o3", "o3-pro", "o3-mini", "o1-mini",
            "computer-use-preview"
        ]
        
        for model in tile_models:
            config = get_model_config(model)
            assert config.family == ModelFamily.TILE_BASED

    def test_image_tokens_family(self):
        """Test image tokens family models."""
        config = get_model_config("gpt-image-1")
        assert config.family == ModelFamily.IMAGE_TOKENS

    def test_family_enum_values(self):
        """Test ModelFamily enum values."""
        assert ModelFamily.PATCH_BASED.value == "patch_based"
        assert ModelFamily.TILE_BASED.value == "tile_based"
        assert ModelFamily.IMAGE_TOKENS.value == "image_tokens"


class TestConfigurationConsistency:
    """Tests for configuration consistency and completeness."""

    def test_patch_based_config_consistency(self):
        """Test patch-based models have consistent configuration."""
        patch_models = ["gpt-4.1-mini", "gpt-4.1-nano", "o4-mini"]
        
        for model in patch_models:
            config = get_model_config(model)
            assert config.patch_size == 32
            assert config.max_patches == 1536
            assert config.multiplier > 1.0
            assert config.base_tokens == 0  # Not used for patch-based
            assert config.tile_tokens == 0  # Not used for patch-based

    def test_tile_based_config_consistency(self):
        """Test tile-based models have consistent configuration."""
        tile_models = ["gpt-4o", "gpt-4.1", "o1"]
        
        for model in tile_models:
            config = get_model_config(model)
            assert config.shortest_side_target == 768
            assert config.max_dimension == 2048
            assert config.patch_size == 512
            assert config.base_tokens > 0
            assert config.tile_tokens > 0
            assert config.multiplier == 1.0  # Not used for tile-based

    def test_all_models_have_valid_config(self):
        """Test that all models have valid configuration."""
        for model_name in MODEL_CONFIGS.keys():
            config = get_model_config(model_name)
            
            # Basic validation
            assert isinstance(config.family, ModelFamily)
            assert config.base_tokens >= 0
            assert config.tile_tokens >= 0
            assert config.multiplier > 0
            assert config.shortest_side_target > 0
            assert config.max_dimension > 0
            assert config.patch_size > 0
"""Tests for the calculator module."""

import pytest
from openai_vision_cost.calculator import (
    calculate_image_cost,
    calculate_tokens_only,
    estimate_cost_range,
    _calculate_patch_based_tokens,
    _calculate_tile_based_tokens,
)
from openai_vision_cost.models import get_model_config
from openai_vision_cost.exceptions import (
    InvalidImageDimensionsError,
    InvalidPricingError,
    InvalidDetailLevelError,
    UnsupportedModelError,
)


class TestValidation:
    """Tests for input validation."""

    def test_invalid_dimensions(self):
        """Test invalid image dimensions."""
        with pytest.raises(InvalidImageDimensionsError):
            calculate_image_cost(0, 100, "gpt-4o", 2.50)
        
        with pytest.raises(InvalidImageDimensionsError):
            calculate_image_cost(100, -1, "gpt-4o", 2.50)
        
        with pytest.raises(InvalidImageDimensionsError):
            calculate_tokens_only(-1, 100, "gpt-4o")

    def test_invalid_pricing(self):
        """Test invalid pricing."""
        with pytest.raises(InvalidPricingError):
            calculate_image_cost(100, 100, "gpt-4o", 0)
        
        with pytest.raises(InvalidPricingError):
            calculate_image_cost(100, 100, "gpt-4o", -1.5)

    def test_invalid_detail_level(self):
        """Test invalid detail level."""
        with pytest.raises(InvalidDetailLevelError):
            calculate_image_cost(100, 100, "gpt-4o", 2.50, "medium")
        
        with pytest.raises(InvalidDetailLevelError):
            calculate_tokens_only(100, 100, "gpt-4o", "invalid")

    def test_unsupported_model(self):
        """Test unsupported model."""
        with pytest.raises(UnsupportedModelError):
            calculate_image_cost(100, 100, "unsupported-model", 2.50)
        
        with pytest.raises(UnsupportedModelError):
            calculate_tokens_only(100, 100, "invalid-model")


class TestPatchBasedCalculation:
    """Tests for patch-based models (GPT-4.1-mini/nano, o4-mini)."""

    def test_basic_patch_calculation(self):
        """Test basic patch calculation."""
        # 1024x1024 image with 32px patches
        tokens = _calculate_patch_based_tokens(1024, 1024, 32, 1536)
        expected = 32 * 32  # (1024/32) * (1024/32) = 32 * 32 = 1024
        assert tokens == expected

    def test_patch_scaling_needed(self):
        """Test patch calculation when scaling is needed."""
        # Large image that needs scaling
        tokens = _calculate_patch_based_tokens(1800, 2400, 32, 1536)
        # Should be scaled down to fit within 1536 patches
        assert tokens <= 1536
        assert tokens > 0

    def test_gpt_4_1_mini_cost(self):
        """Test GPT-4.1-mini cost calculation."""
        result = calculate_image_cost(1024, 1024, "gpt-4.1-mini", 0.40)
        
        # 1024x1024 = 1024 image tokens
        # 1024 * 1.62 = 1658.88 ≈ 1658 text tokens
        expected_image_tokens = 1024
        expected_text_tokens = int(1024 * 1.62)
        expected_cost = expected_text_tokens * (0.40 / 1_000_000)
        
        assert result["image_tokens"] == expected_image_tokens
        assert result["text_tokens"] == expected_text_tokens
        assert abs(result["total_cost_usd"] - expected_cost) < 1e-10

    def test_gpt_4_1_nano_multiplier(self):
        """Test GPT-4.1-nano multiplier."""
        result = calculate_tokens_only(1024, 1024, "gpt-4.1-nano")
        
        expected_image_tokens = 1024
        expected_text_tokens = int(1024 * 2.46)
        
        assert result["image_tokens"] == expected_image_tokens
        assert result["text_tokens"] == expected_text_tokens

    def test_o4_mini_multiplier(self):
        """Test o4-mini multiplier."""
        result = calculate_tokens_only(1024, 1024, "o4-mini")
        
        expected_image_tokens = 1024
        expected_text_tokens = int(1024 * 1.72)
        
        assert result["image_tokens"] == expected_image_tokens
        assert result["text_tokens"] == expected_text_tokens


class TestTileBasedCalculation:
    """Tests for tile-based models (GPT-4o family)."""

    def test_gpt_4o_high_detail_1024x1024(self):
        """Test GPT-4o with 1024x1024 image from OpenAI docs."""
        config = get_model_config("gpt-4o")
        tokens = _calculate_tile_based_tokens(1024, 1024, config, "high")
        
        # From OpenAI docs: 1024x1024 in high detail = 765 tokens
        # (4 tiles * 170) + 85 = 765
        expected = 765
        assert tokens == expected

    def test_gpt_4o_high_detail_2048x4096(self):
        """Test GPT-4o with 2048x4096 image from OpenAI docs."""
        config = get_model_config("gpt-4o")
        tokens = _calculate_tile_based_tokens(2048, 4096, config, "high")
        
        # From OpenAI docs: 2048x4096 in high detail = 1105 tokens
        # Should scale to 1024x2048, then to 768x1536
        # 6 tiles * 170 + 85 = 1105
        expected = 1105
        assert tokens == expected

    def test_gpt_4o_low_detail(self):
        """Test GPT-4o with low detail."""
        config = get_model_config("gpt-4o")
        tokens = _calculate_tile_based_tokens(4096, 8192, config, "low")
        
        # Low detail is always base tokens only
        expected = 85
        assert tokens == expected

    def test_gpt_4o_mini_high_detail(self):
        """Test GPT-4o-mini with high detail."""
        result = calculate_tokens_only(1024, 1024, "gpt-4o-mini", "high")
        
        # GPT-4o-mini has different base/tile tokens
        # 4 tiles * 5667 + 2833 = 25501
        expected = 4 * 5667 + 2833
        assert result["text_tokens"] == expected

    def test_gpt_4o_cost_calculation(self):
        """Test complete cost calculation for GPT-4o."""
        result = calculate_image_cost(1024, 1024, "gpt-4o", 2.50, "high")
        
        expected_tokens = 765
        expected_cost = 765 * (2.50 / 1_000_000)
        
        assert result["text_tokens"] == expected_tokens
        assert abs(result["total_cost_usd"] - expected_cost) < 1e-10


class TestImageTokensModel:
    """Tests for GPT Image 1 model."""

    def test_gpt_image_1_calculation(self):
        """Test GPT Image 1 token calculation."""
        # GPT Image 1 uses 512px shortest side instead of 768px
        result = calculate_tokens_only(1024, 1024, "gpt-image-1", "high")
        
        # Should scale to 512x512, then calculate tiles
        # 1 tile * 129 + 65 = 194
        expected = 1 * 129 + 65
        assert result["text_tokens"] == expected

    def test_gpt_image_1_cost(self):
        """Test GPT Image 1 cost calculation."""
        result = calculate_image_cost(1024, 1024, "gpt-image-1", 10.00, "high")
        
        expected_tokens = 1 * 129 + 65
        expected_cost = expected_tokens * (10.00 / 1_000_000)
        
        assert result["total_cost_usd"] == expected_cost


class TestModelAliases:
    """Tests for model aliases and variations."""

    def test_model_with_date_suffix(self):
        """Test model with date suffix."""
        result1 = calculate_tokens_only(1024, 1024, "gpt-4o")
        result2 = calculate_tokens_only(1024, 1024, "gpt-4o-2024-08-06")
        
        assert result1 == result2

    def test_preview_models(self):
        """Test preview model variants."""
        result1 = calculate_tokens_only(1024, 1024, "gpt-4o")
        result2 = calculate_tokens_only(1024, 1024, "gpt-4o-audio-preview")
        
        assert result1 == result2


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_estimate_cost_range(self):
        """Test cost range estimation."""
        result = estimate_cost_range(1024, 1024, "gpt-4o", 2.50)
        
        assert "high" in result
        assert "low" in result
        assert result["high"]["total_cost_usd"] > result["low"]["total_cost_usd"]
        assert result["low"]["text_tokens"] == 85  # Base tokens for low detail

    def test_calculate_tokens_only(self):
        """Test tokens-only calculation."""
        result = calculate_tokens_only(1024, 1024, "gpt-4o")
        
        assert "image_tokens" in result
        assert "text_tokens" in result
        assert isinstance(result["image_tokens"], int)
        assert isinstance(result["text_tokens"], int)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_image(self):
        """Test very small image."""
        result = calculate_image_cost(1, 1, "gpt-4o", 2.50)
        
        # Should still work and produce valid result
        assert result["text_tokens"] > 0
        assert result["total_cost_usd"] > 0

    def test_very_large_image(self):
        """Test very large image."""
        result = calculate_image_cost(10000, 10000, "gpt-4o", 2.50)
        
        # Should be scaled down appropriately
        assert result["text_tokens"] > 0
        assert result["total_cost_usd"] > 0

    def test_extreme_aspect_ratio(self):
        """Test extreme aspect ratio."""
        result = calculate_image_cost(10000, 100, "gpt-4o", 2.50)
        
        # Should handle extreme aspect ratios
        assert result["text_tokens"] > 0
        assert result["total_cost_usd"] > 0

    def test_square_vs_rectangle(self):
        """Test that equivalent area images may have different costs."""
        square = calculate_tokens_only(1000, 1000, "gpt-4o")
        rectangle = calculate_tokens_only(2000, 500, "gpt-4o")
        
        # Results may differ due to tiling/scaling behavior
        assert square["text_tokens"] > 0
        assert rectangle["text_tokens"] > 0
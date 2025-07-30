# OpenAI Vision Cost Calculator

[![PyPI version](https://badge.fury.io/py/openai-vision-cost.svg)](https://badge.fury.io/py/openai-vision-cost)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library for calculating the cost of image inputs to OpenAI vision models. This library implements the exact cost calculation logic described in the OpenAI documentation, supporting all current vision models including GPT-4o, GPT-4.1, GPT-4o-mini, o1, o3, and more.

## Features

- **Accurate Cost Calculation**: Implements the exact token calculation logic from OpenAI documentation
- **All Vision Models Supported**: GPT-4o, GPT-4.1-mini/nano, o4-mini, o1/o3 series, computer-use-preview, and GPT Image 1
- **Flexible Pricing**: Accepts current pricing as input (per million tokens)
- **Detail Level Support**: Handles both "high" and "low" detail image processing
- **Comprehensive Validation**: Input validation with helpful error messages
- **Easy to Use**: Simple API with clear documentation

## Installation

```bash
pip install openai-vision-cost
```

## Quick Start

```python
from openai_vision_cost import calculate_image_cost

# Calculate cost for a 1024x1024 image using GPT-4o
result = calculate_image_cost(
    width=1024,
    height=1024,
    model="gpt-4o",
    input_price_per_million=2.50,  # $2.50 per 1M tokens
    detail="high"
)

print(f"Tokens: {result['text_tokens']}")
print(f"Cost: ${result['total_cost_usd']:.6f}")
```

## Usage Examples

### Basic Cost Calculation

```python
from openai_vision_cost import calculate_image_cost

# High detail image processing
result = calculate_image_cost(
    width=1024, 
    height=1024, 
    model="gpt-4o", 
    input_price_per_million=2.50
)

print(f"Image tokens: {result['image_tokens']}")
print(f"Text tokens (billed): {result['text_tokens']}")
print(f"Total cost: ${result['total_cost_usd']:.6f}")
# Output: Image tokens: 765, Text tokens: 765, Total cost: $0.001913
```

### Compare High vs Low Detail

```python
from openai_vision_cost import estimate_cost_range

# Get cost estimates for both detail levels
costs = estimate_cost_range(
    width=2048, 
    height=1024, 
    model="gpt-4o", 
    input_price_per_million=2.50
)

print("High detail:", costs['high'])
print("Low detail:", costs['low'])
```

### Token Calculation Only

```python
from openai_vision_cost import calculate_tokens_only

# Get token counts without cost calculation
tokens = calculate_tokens_only(
    width=1800, 
    height=2400, 
    model="gpt-4.1-mini"
)

print(f"Image tokens: {tokens['image_tokens']}")
print(f"Text tokens: {tokens['text_tokens']}")
```

### Working with Different Models

```python
from openai_vision_cost import calculate_image_cost, get_supported_models

# List all supported models
models = get_supported_models()
print("Supported models:", models[:5])  # Show first 5

# Calculate costs for different model families
models_to_test = [
    ("gpt-4o", 2.50),           # Tile-based model
    ("gpt-4.1-mini", 0.40),     # Patch-based with multiplier
    ("gpt-image-1", 10.00),     # Image tokens model
]

for model, price in models_to_test:
    result = calculate_image_cost(1024, 1024, model, price)
    print(f"{model}: {result['text_tokens']} tokens, ${result['total_cost_usd']:.6f}")
```

## Model Families and Pricing

The library supports three different model families, each with different cost calculation methods:

### Patch-Based Models (32px patches)
- **gpt-4.1-mini**: Multiplier 1.62x
- **gpt-4.1-nano**: Multiplier 2.46x  
- **o4-mini**: Multiplier 1.72x

### Tile-Based Models (512px tiles)
- **gpt-4o**: 85 base + 170 per tile
- **gpt-4.1**: 85 base + 170 per tile
- **gpt-4o-mini**: 2833 base + 5667 per tile
- **o1/o3 series**: 75 base + 150 per tile
- **computer-use-preview**: 65 base + 129 per tile

### Image Tokens Model
- **gpt-image-1**: 65 base + 129 per tile (512px shortest side)

## Current OpenAI Pricing (as of 2024)

Here are the current input token prices per 1M tokens from OpenAI:

| Model | Price per 1M Tokens |
|-------|---------------------|
| gpt-4.1 | $2.00 |
| gpt-4.1-mini | $0.40 |
| gpt-4.1-nano | $0.10 |
| gpt-4o | $2.50 |
| gpt-4o-mini | $0.15 |
| o1 | $15.00 |
| o1-pro | $150.00 |
| o3 | $2.00 |
| o3-pro | $20.00 |
| o4-mini | $1.10 |
| computer-use-preview | $3.00 |
| gpt-image-1 | $5.00 (text) / $10.00 (image) |

**Note**: Prices may change. Always check the [OpenAI Pricing Page](https://openai.com/api/pricing/) for the most current rates.

## API Reference

### Main Functions

#### `calculate_image_cost(width, height, model, input_price_per_million, detail="high")`

Calculate the cost of processing an image with OpenAI vision models.

**Parameters:**
- `width` (int): Image width in pixels
- `height` (int): Image height in pixels  
- `model` (str): Model name (e.g., "gpt-4o", "gpt-4.1-mini")
- `input_price_per_million` (float): Price per million tokens in USD
- `detail` (str): Detail level, "high" or "low" (default: "high")

**Returns:**
Dict with keys:
- `image_tokens` (int): Raw image tokens calculated from dimensions
- `text_tokens` (int): Final tokens used for billing
- `total_cost_usd` (float): Total cost in USD

#### `calculate_tokens_only(width, height, model, detail="high")`

Calculate only token counts without cost.

**Parameters:** Same as above except `input_price_per_million`

**Returns:**
Dict with keys:
- `image_tokens` (int): Raw image tokens
- `text_tokens` (int): Final tokens for billing

#### `estimate_cost_range(width, height, model, input_price_per_million)`

Get cost estimates for both high and low detail levels.

**Returns:**
Dict with "high" and "low" keys, each containing cost calculation results.

### Utility Functions

#### `get_supported_models()`

Returns a list of all supported model names.

#### `is_model_supported(model_name)`

Check if a model is supported.

## Error Handling

The library provides specific exceptions for different error conditions:

```python
from openai_vision_cost import (
    calculate_image_cost,
    UnsupportedModelError,
    InvalidImageDimensionsError,
    InvalidPricingError,
    InvalidDetailLevelError
)

try:
    result = calculate_image_cost(0, 100, "gpt-4o", 2.50)
except InvalidImageDimensionsError as e:
    print(f"Invalid dimensions: {e}")
except UnsupportedModelError as e:
    print(f"Unsupported model: {e}")
except InvalidPricingError as e:
    print(f"Invalid pricing: {e}")
```

## Validation Examples from OpenAI Documentation

The library has been validated against the examples provided in the OpenAI documentation:

```python
# Example 1: 1024x1024 image with gpt-4o = 765 tokens
result = calculate_tokens_only(1024, 1024, "gpt-4o", "high")
assert result['text_tokens'] == 765

# Example 2: 2048x4096 image with gpt-4o = 1105 tokens  
result = calculate_tokens_only(2048, 4096, "gpt-4o", "high")
assert result['text_tokens'] == 1105

# Example 3: Any image with low detail = base tokens only
result = calculate_tokens_only(4096, 8192, "gpt-4o", "low")
assert result['text_tokens'] == 85
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
git clone https://github.com/alexferrari88/openai-vision-cost-calculator.git
cd openai-vision-cost
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
black src tests
isort src tests  
flake8 src tests
mypy src
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This library is not officially affiliated with OpenAI. It implements the cost calculation logic based on publicly available OpenAI documentation. Always verify costs with the official OpenAI pricing calculator for the most accurate estimates.

## Changelog

### 1.0.0 (2024-01-XX)
- Initial release
- Support for all current OpenAI vision models
- Comprehensive test coverage
- Complete documentation
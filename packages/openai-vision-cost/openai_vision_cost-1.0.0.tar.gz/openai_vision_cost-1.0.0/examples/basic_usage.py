#!/usr/bin/env python3
"""
Basic usage examples for OpenAI Vision Cost Calculator.

This script demonstrates how to use the library to calculate costs
for different image sizes and models.
"""

from openai_vision_cost import (
    calculate_image_cost,
    calculate_tokens_only,
    estimate_cost_range,
    get_supported_models,
    is_model_supported,
)


def main():
    """Run basic usage examples."""
    print("OpenAI Vision Cost Calculator - Basic Usage Examples")
    print("=" * 55)
    
    # Example 1: Basic cost calculation
    print("\n1. Basic Cost Calculation")
    print("-" * 25)
    
    result = calculate_image_cost(
        width=1024,
        height=1024,
        model="gpt-4o",
        input_price_per_million=2.50,
        detail="high"
    )
    
    print(f"Image: 1024x1024 pixels")
    print(f"Model: gpt-4o")
    print(f"Detail: high")
    print(f"Image tokens: {result['image_tokens']}")
    print(f"Text tokens (billed): {result['text_tokens']}")
    print(f"Total cost: ${result['total_cost_usd']:.6f}")
    
    # Example 2: Compare different models
    print("\n2. Compare Different Models")
    print("-" * 28)
    
    models_to_compare = [
        ("gpt-4o", 2.50),
        ("gpt-4.1-mini", 0.40),
        ("gpt-4o-mini", 0.15),
        ("o1", 15.00),
        ("gpt-image-1", 10.00),
    ]
    
    image_width, image_height = 1024, 1024
    
    print(f"Cost comparison for {image_width}x{image_height} image:")
    print(f"{'Model':<15} {'Price/1M':<10} {'Tokens':<8} {'Cost':<12}")
    print("-" * 50)
    
    for model, price in models_to_compare:
        if is_model_supported(model):
            result = calculate_image_cost(image_width, image_height, model, price)
            print(f"{model:<15} ${price:<9.2f} {result['text_tokens']:<8} ${result['total_cost_usd']:<11.6f}")
    
    # Example 3: High vs Low detail comparison
    print("\n3. High vs Low Detail Comparison")
    print("-" * 32)
    
    model = "gpt-4o"
    price = 2.50
    
    costs = estimate_cost_range(2048, 1536, model, price)
    
    print(f"Image: 2048x1536 pixels")
    print(f"Model: {model}")
    print(f"High detail: {costs['high']['text_tokens']} tokens, ${costs['high']['total_cost_usd']:.6f}")
    print(f"Low detail:  {costs['low']['text_tokens']} tokens, ${costs['low']['total_cost_usd']:.6f}")
    print(f"Savings with low detail: ${costs['high']['total_cost_usd'] - costs['low']['total_cost_usd']:.6f}")
    
    # Example 4: Token calculation only
    print("\n4. Token Calculation Only")
    print("-" * 25)
    
    tokens = calculate_tokens_only(1800, 2400, "gpt-4.1-mini", "high")
    print(f"Image: 1800x2400 pixels")
    print(f"Model: gpt-4.1-mini (patch-based with 1.62x multiplier)")
    print(f"Image tokens (patches): {tokens['image_tokens']}")
    print(f"Text tokens (after multiplier): {tokens['text_tokens']}")
    
    # Example 5: Different image sizes
    print("\n5. Different Image Sizes")
    print("-" * 24)
    
    test_images = [
        (512, 512, "Small square"),
        (1024, 1024, "Medium square"), 
        (2048, 1024, "Wide rectangle"),
        (1024, 2048, "Tall rectangle"),
        (4096, 4096, "Large square"),
    ]
    
    model = "gpt-4o"
    price = 2.50
    
    print(f"{'Description':<15} {'Size':<12} {'Tokens':<8} {'Cost':<12}")
    print("-" * 50)
    
    for width, height, description in test_images:
        result = calculate_image_cost(width, height, model, price, "high")
        size_str = f"{width}x{height}"
        print(f"{description:<15} {size_str:<12} {result['text_tokens']:<8} ${result['total_cost_usd']:<11.6f}")
    
    # Example 6: Supported models
    print("\n6. Supported Models")
    print("-" * 17)
    
    models = get_supported_models()
    print(f"Total supported models: {len(models)}")
    print("First 10 models:")
    for model in models[:10]:
        print(f"  - {model}")
    print("  ...")
    
    # Example 7: Validation of OpenAI documentation examples
    print("\n7. Validation Against OpenAI Examples")
    print("-" * 37)
    
    # Example from OpenAI docs: 1024x1024 gpt-4o high detail = 765 tokens
    result = calculate_tokens_only(1024, 1024, "gpt-4o", "high")
    expected = 765
    print(f"1024x1024 gpt-4o high: {result['text_tokens']} tokens (expected: {expected}) ✓" if result['text_tokens'] == expected else "✗")
    
    # Example from OpenAI docs: 2048x4096 gpt-4o high detail = 1105 tokens
    result = calculate_tokens_only(2048, 4096, "gpt-4o", "high")
    expected = 1105
    print(f"2048x4096 gpt-4o high: {result['text_tokens']} tokens (expected: {expected}) ✓" if result['text_tokens'] == expected else "✗")
    
    # Low detail should always be base tokens
    result = calculate_tokens_only(4096, 8192, "gpt-4o", "low")
    expected = 85  # Base tokens for gpt-4o
    print(f"Any size gpt-4o low: {result['text_tokens']} tokens (expected: {expected}) ✓" if result['text_tokens'] == expected else "✗")
    
    print("\n" + "=" * 55)
    print("Examples completed successfully!")


if __name__ == "__main__":
    main()
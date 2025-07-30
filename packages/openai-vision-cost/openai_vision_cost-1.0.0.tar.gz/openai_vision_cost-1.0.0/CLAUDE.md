# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Testing
```bash
pytest                    # Run all tests
pytest tests/test_calculator.py  # Run specific test file
pytest -v                # Verbose test output
pytest --cov             # Run with coverage (if pytest-cov installed)
```

### Code Quality
```bash
black src tests          # Format code
isort src tests          # Sort imports
flake8 src tests         # Lint code
mypy src                 # Type checking
```

### Development Setup
```bash
pip install -e ".[dev]"  # Install in development mode with dev dependencies
```

### Build and Distribution
```bash
pip install build       # Install build tool
python -m build         # Build wheel and source distribution
```

## Code Architecture

This is a Python library for calculating OpenAI vision model costs. The codebase implements the exact token calculation logic from OpenAI's official documentation.

### Core Structure
- `src/openai_vision_cost/calculator.py` - Main calculation logic with three different algorithms for different model families
- `src/openai_vision_cost/models.py` - Model definitions and configurations for all supported OpenAI vision models
- `src/openai_vision_cost/exceptions.py` - Custom exception classes for validation errors
- `src/openai_vision_cost/__init__.py` - Public API exports

### Model Families
The library handles three distinct model families, each with different cost calculation methods:

1. **Patch-based models** (32px patches): gpt-4.1-mini, gpt-4.1-nano, o4-mini
   - Uses patch counting with multipliers
   - Capped at 1536 patches maximum

2. **Tile-based models** (512px tiles): gpt-4o, gpt-4.1, gpt-4o-mini, o1/o3 series, computer-use-preview
   - Uses base tokens + tile counting
   - Supports high/low detail levels

3. **Image tokens model**: gpt-image-1
   - Special case with 512px shortest side scaling
   - No detail level configuration

### Key Implementation Details
- All calculations are based on OpenAI's official documentation examples
- Input validation covers dimensions, pricing, detail levels, and model support
- The library returns both raw image tokens and final billable text tokens
- Cost calculations accept current pricing as input (per million tokens)
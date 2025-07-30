"""Custom exceptions for OpenAI Vision Cost Calculator."""


class OpenAIVisionCostError(Exception):
    """Base exception for OpenAI Vision Cost Calculator."""
    pass


class UnsupportedModelError(OpenAIVisionCostError):
    """Raised when an unsupported model is specified."""
    
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        super().__init__(f"Unsupported model: {model_name}")


class InvalidImageDimensionsError(OpenAIVisionCostError):
    """Raised when invalid image dimensions are provided."""
    
    def __init__(self, width: int, height: int, message: str = "") -> None:
        self.width = width
        self.height = height
        if not message:
            message = f"Invalid image dimensions: {width}x{height}"
        super().__init__(message)


class InvalidPricingError(OpenAIVisionCostError):
    """Raised when invalid pricing is provided."""
    
    def __init__(self, price: float, message: str = "") -> None:
        self.price = price
        if not message:
            message = f"Invalid price: {price}. Price must be a positive number."
        super().__init__(message)


class InvalidDetailLevelError(OpenAIVisionCostError):
    """Raised when an invalid detail level is specified."""
    
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Invalid detail level: {detail}. Must be 'high' or 'low'.")
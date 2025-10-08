"""Error handling and custom exceptions for CityFusion-Agent."""

from typing import Optional, Dict, Any


class CityFusionError(Exception):
    """Base exception for CityFusion-Agent."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.message = message


class ConfigurationError(CityFusionError):
    """Raised when there's a configuration-related error."""
    pass


class AgentError(CityFusionError):
    """Raised when there's an agent-related error."""
    pass


class ToolError(CityFusionError):
    """Raised when there's a tool-related error."""
    pass


class APIError(CityFusionError):
    """Raised when there's an external API error."""
    pass


class ValidationError(CityFusionError):
    """Raised when there's a validation error."""
    pass


def handle_exception(func):
    """Decorator for handling exceptions in a standardized way."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CityFusionError:
            # Re-raise CityFusion-specific errors
            raise
        except Exception as e:
            # Convert generic exceptions to CityFusionError
            raise CityFusionError(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                details={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)}
            ) from e
    return wrapper
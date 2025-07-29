class BaseError(Exception):
    """Base exception for API errors."""
    pass

class AuthenticationError(BaseError):
    """Raised for authentication-related issues."""
    pass

class NotFoundError(BaseError):
    """Raised when a requested resource is not found."""
    pass

class ValidationError(BaseError):
    """Raised for invalid input."""
    pass
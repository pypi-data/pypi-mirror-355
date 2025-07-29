"""
Custom exceptions for {{ project_name }}.
"""
from fastapi import HTTPException, status

class NotFoundError(HTTPException):
    """Raised when a resource is not found."""

    def __init__(self, detail: str = "Resource not found"):
        """Initialize the exception."""
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ValidationError(HTTPException):
    """Raised when input validation fails."""

    def __init__(self, detail: str = "Validation error"):
        """Initialize the exception."""
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class AuthenticationError(HTTPException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Authentication failed"):
        """Initialize the exception."""
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
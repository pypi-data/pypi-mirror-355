"""Custom exceptions for the Docker adapter."""

class DockerAdapterError(Exception):
    """Base exception for all Docker adapter errors."""
    pass

class ContainerNotFoundError(DockerAdapterError):
    """Raised when a container is not found."""
    pass

class ImageNotFoundError(DockerAdapterError):
    """Raised when an image is not found."""
    pass

class ContainerOperationError(DockerAdapterError):
    """Raised when a container operation fails."""
    pass

class ImageOperationError(DockerAdapterError):
    """Raised when an image operation fails."""
    pass

class DockerConnectionError(DockerAdapterError):
    """Raised when there's an error connecting to the Docker daemon."""
    pass 
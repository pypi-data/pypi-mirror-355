"""
Docker Adapter - A Python library for managing Docker containers and images.
"""

from .client import DockerClient
from .container import Container
from .exceptions import DockerAdapterError
from .image import Image

__version__ = "0.2.0"
__all__ = ["DockerClient", "Container", "DockerAdapterError", "Image"]
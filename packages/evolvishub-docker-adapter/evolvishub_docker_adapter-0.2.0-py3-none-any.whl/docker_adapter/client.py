"""Docker client for managing Docker containers and images."""

from typing import Any, Dict, List, Optional, cast

import docker
from docker import errors as docker_errors

from docker_adapter.container import Container
from docker_adapter.exceptions import (
    ContainerNotFoundError,
    DockerConnectionError,
    ImageNotFoundError,
)
from docker_adapter.image import Image


class DockerClient:
    """A client for managing Docker containers and images."""

    def __init__(self, base_url: Optional[str] = None, **kwargs: Any):
        """Initialize the Docker client.

        Args:
            base_url: The URL of the Docker daemon.
            **kwargs: Additional arguments to pass to the Docker client.

        Raises:
            DockerConnectionError: If the connection to Docker fails.
        """
        try:
            if base_url:
                self._client = docker.DockerClient(base_url=base_url, **kwargs)
            else:
                self._client = docker.from_env(**kwargs)
        except Exception as e:
            raise DockerConnectionError(f"Failed to connect to Docker: {str(e)}") from e

    def list_containers(self, all: bool = False, **kwargs: Any) -> List[Container]:
        """List containers.

        Args:
            all: Show all containers (default shows just running).
            **kwargs: Additional arguments to pass to the list operation.

        Returns:
            A list of Container objects.
        """
        containers = self._client.containers.list(all=all, **kwargs)
        return [Container(container) for container in containers]

    def get_container(self, container_id: str) -> Container:
        """Get a container by ID.

        Args:
            container_id: The ID of the container.

        Returns:
            A Container object.

        Raises:
            ContainerNotFoundError: If the container is not found.
        """
        try:
            container = self._client.containers.get(container_id)
            return Container(container)
        except docker_errors.NotFound:
            raise ContainerNotFoundError(f"Container {container_id} not found") from None
        except Exception as e:
            raise ContainerNotFoundError(f"Failed to get container: {str(e)}") from e

    def list_images(self, name: Optional[str] = None, **kwargs: Any) -> List[Image]:
        """List images.

        Args:
            name: Filter images by name.
            **kwargs: Additional arguments to pass to the list operation.

        Returns:
            A list of Image objects.
        """
        images = self._client.images.list(name=name, **kwargs)
        return [Image(image) for image in images]

    def get_image(self, image_id: str) -> Image:
        """Get an image by ID.

        Args:
            image_id: The ID of the image.

        Returns:
            An Image object.

        Raises:
            ImageNotFoundError: If the image is not found.
        """
        try:
            image = self._client.images.get(image_id)
            return Image(image)
        except docker_errors.NotFound:
            raise ImageNotFoundError(f"Image {image_id} not found") from None
        except Exception as e:
            raise ImageNotFoundError(f"Failed to get image: {str(e)}") from e

    def pull_image(self, repository: str, tag: Optional[str] = None, **kwargs: Any) -> Image:
        """Pull an image from a registry.

        Args:
            repository: The repository to pull from.
            tag: The tag to pull.
            **kwargs: Additional arguments to pass to the pull operation.

        Returns:
            An Image object.

        Raises:
            ImageNotFoundError: If the image is not found.
        """
        try:
            image = self._client.images.pull(repository, tag=tag, **kwargs)
            return Image(image)
        except Exception as e:
            raise ImageNotFoundError(f"Failed to pull image: {str(e)}") from e

    def build_image(self, path: str, tag: Optional[str] = None, **kwargs: Any) -> Image:
        """Build an image from a Dockerfile.

        Args:
            path: The path to the directory containing the Dockerfile.
            tag: The tag to apply to the image.
            **kwargs: Additional arguments to pass to the build operation.

        Returns:
            An Image object.

        Raises:
            ImageNotFoundError: If the image build fails.
        """
        try:
            image, _ = self._client.images.build(path=path, tag=tag, **kwargs)
            return Image(image)
        except Exception as e:
            raise ImageNotFoundError(f"Failed to build image: {str(e)}") from e

    def prune_containers(self, **kwargs: Any) -> Dict[str, Any]:
        """Remove all stopped containers.

        Args:
            **kwargs: Additional arguments to pass to the prune operation.

        Returns:
            A dictionary containing the results of the prune operation.
        """
        return cast(Dict[str, Any], self._client.containers.prune(**kwargs))

    def prune_images(self, **kwargs: Any) -> Dict[str, Any]:
        """Remove unused images.

        Args:
            **kwargs: Additional arguments to pass to the prune operation.

        Returns:
            A dictionary containing the results of the prune operation.
        """
        return cast(Dict[str, Any], self._client.images.prune(**kwargs))

    def info(self) -> Dict[str, Any]:
        """Get Docker system information.

        Returns:
            A dictionary containing Docker system information.
        """
        return cast(Dict[str, Any], self._client.info())

    def version(self) -> Dict[str, Any]:
        """Get Docker version information.

        Returns:
            A dictionary containing Docker version information.
        """
        return cast(Dict[str, Any], self._client.version())
"""Image class for managing Docker images."""

from typing import Any, Dict, List, Optional, cast

from docker_adapter.exceptions import ImageOperationError


class Image:
    """A class representing a Docker image."""

    def __init__(self, image: Any):
        """Initialize the Image.

        Args:
            image: The Docker image object.
        """
        self._image = image

    @property
    def id(self) -> str:
        """Get the image ID."""
        return cast(str, self._image.id)

    @property
    def tags(self) -> List[str]:
        """Get the image tags."""
        return cast(List[str], self._image.tags)

    @property
    def labels(self) -> Dict[str, str]:
        """Get the image labels."""
        return cast(Dict[str, str], self._image.labels)

    def tag(self, repository: str, tag: Optional[str] = None) -> None:
        """Tag the image.

        Args:
            repository: The repository to tag the image with.
            tag: The tag to apply to the image.

        Raises:
            ImageOperationError: If the tagging operation fails.
        """
        try:
            self._image.tag(repository, tag=tag)
        except Exception as e:
            raise ImageOperationError(f"Failed to tag image: {str(e)}") from e

    def remove(self, force: bool = False, noprune: bool = False) -> None:
        """Remove the image.

        Args:
            force: Force removal of the image.
            noprune: Do not delete untagged parent images.

        Raises:
            ImageOperationError: If the removal operation fails.
        """
        try:
            self._image.remove(force=force, noprune=noprune)
        except Exception as e:
            raise ImageOperationError(f"Failed to remove image: {str(e)}") from e

    def save(self, chunk_size: int = 2097152) -> bytes:
        """Save the image to a tar archive.

        Args:
            chunk_size: The chunk size to use when saving the image.

        Returns:
            The image data as bytes.

        Raises:
            ImageOperationError: If the save operation fails.
        """
        try:
            return cast(bytes, self._image.save(chunk_size=chunk_size))
        except Exception as e:
            raise ImageOperationError(f"Failed to save image: {str(e)}") from e

    def history(self) -> List[Dict[str, Any]]:
        """Get the image history.

        Returns:
            A list of dictionaries containing the image history.

        Raises:
            ImageOperationError: If the history operation fails.
        """
        try:
            return cast(List[Dict[str, Any]], self._image.history())
        except Exception as e:
            raise ImageOperationError(f"Failed to get image history: {str(e)}") from e

    def inspect(self) -> Dict[str, Any]:
        """Inspect the image.

        Returns:
            A dictionary containing the image details.

        Raises:
            ImageOperationError: If the inspect operation fails.
        """
        try:
            if not self._image.attrs:
                self._image.reload()
            return cast(Dict[str, Any], self._image.attrs)
        except Exception as e:
            raise ImageOperationError(f"Failed to inspect image: {str(e)}") from e

    def push(self, repository: str, tag: Optional[str] = None, **kwargs: Any) -> None:
        """Push the image to a registry.

        Args:
            repository: The repository to push to.
            tag: The tag to push.
            **kwargs: Additional arguments to pass to the push operation.

        Raises:
            ImageOperationError: If the push operation fails.
        """
        try:
            self._image.push(repository, tag=tag, **kwargs)
        except Exception as e:
            raise ImageOperationError(f"Failed to push image: {str(e)}") from e 
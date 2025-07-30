"""Container class for managing Docker containers."""

from typing import Any, Dict, Optional, Union, cast

from docker_adapter.exceptions import ContainerOperationError


class Container:
    """A class representing a Docker container."""

    def __init__(self, container: Any):
        """Initialize the Container.

        Args:
            container: The Docker container object.
        """
        self._container = container

    @property
    def id(self) -> str:
        """Get the container ID."""
        return cast(str, self._container.id)

    @property
    def name(self) -> str:
        """Get the container name."""
        return cast(str, self._container.name)

    @property
    def status(self) -> str:
        """Get the container status."""
        return cast(str, self._container.status)

    @property
    def image(self) -> Any:
        """Get the container image."""
        return self._container.image

    def start(self) -> None:
        """Start the container.

        Raises:
            ContainerOperationError: If the start operation fails.
        """
        try:
            self._container.start()
        except Exception as e:
            raise ContainerOperationError(f"Failed to start container: {str(e)}") from e

    def stop(self, timeout: Optional[int] = None) -> None:
        """Stop the container.

        Args:
            timeout: Timeout in seconds to wait for the container to stop.

        Raises:
            ContainerOperationError: If the stop operation fails.
        """
        try:
            self._container.stop(timeout=timeout)
        except Exception as e:
            raise ContainerOperationError(f"Failed to stop container: {str(e)}") from e

    def restart(self, timeout: Optional[int] = None) -> None:
        """Restart the container.

        Args:
            timeout: Timeout in seconds to wait for the container to restart.

        Raises:
            ContainerOperationError: If the restart operation fails.
        """
        try:
            self._container.restart(timeout=timeout)
        except Exception as e:
            raise ContainerOperationError(f"Failed to restart container: {str(e)}") from e

    def pause(self) -> None:
        """Pause the container.

        Raises:
            ContainerOperationError: If the pause operation fails.
        """
        try:
            self._container.pause()
        except Exception as e:
            raise ContainerOperationError(f"Failed to pause container: {str(e)}") from e

    def unpause(self) -> None:
        """Unpause the container.

        Raises:
            ContainerOperationError: If the unpause operation fails.
        """
        try:
            self._container.unpause()
        except Exception as e:
            raise ContainerOperationError(f"Failed to unpause container: {str(e)}") from e

    def kill(self, signal: Optional[str] = None) -> None:
        """Kill the container.

        Args:
            signal: Signal to send to the container.

        Raises:
            ContainerOperationError: If the kill operation fails.
        """
        try:
            self._container.kill(signal=signal)
        except Exception as e:
            raise ContainerOperationError(f"Failed to kill container: {str(e)}") from e

    def remove(self, force: bool = False, v: bool = False) -> None:
        """Remove the container.

        Args:
            force: Force removal of the container.
            v: Remove volumes associated with the container.

        Raises:
            ContainerOperationError: If the remove operation fails.
        """
        try:
            self._container.remove(force=force, v=v)
        except Exception as e:
            raise ContainerOperationError(f"Failed to remove container: {str(e)}") from e

    def logs(self, follow: bool = False, tail: Optional[int] = None) -> str:
        """Get container logs.

        Args:
            follow: Follow log output.
            tail: Number of lines to show from the end of the logs.

        Returns:
            The container logs as a string.

        Raises:
            ContainerOperationError: If the logs operation fails.
        """
        try:
            return cast(bytes, self._container.logs(follow=follow, tail=tail)).decode('utf-8')
        except Exception as e:
            raise ContainerOperationError(f"Failed to get container logs: {str(e)}") from e

    def stats(self, stream: bool = False) -> Union[Dict[str, Any], Any]:
        """Get container stats.

        Args:
            stream: Stream the stats.

        Returns:
            Container stats.

        Raises:
            ContainerOperationError: If the stats operation fails.
        """
        try:
            return self._container.stats(stream=stream)
        except Exception as e:
            raise ContainerOperationError(f"Failed to get container stats: {str(e)}") from e

    def exec_run(self, command: str, **kwargs: Any) -> Any:
        """Execute a command in the container.

        Args:
            command: Command to execute.
            **kwargs: Additional arguments to pass to the exec_run operation.

        Returns:
            The result of the command execution.

        Raises:
            ContainerOperationError: If the exec_run operation fails.
        """
        try:
            return self._container.exec_run(command, **kwargs)
        except Exception as e:
            raise ContainerOperationError(
                f"Failed to execute command in container: {str(e)}"
            ) from e

    def inspect(self) -> Dict[str, Any]:
        """Inspect the container.

        Returns:
            A dictionary containing the container details.

        Raises:
            ContainerOperationError: If the inspect operation fails.
        """
        try:
            if not self._container.attrs:
                self._container.reload()
            return cast(Dict[str, Any], self._container.attrs)
        except Exception as e:
            raise ContainerOperationError(f"Failed to inspect container: {str(e)}") from e 
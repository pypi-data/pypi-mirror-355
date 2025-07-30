from importlib.metadata import version
from typing import overload, Literal, Unpack
from functools import lru_cache
from ._base import PixelClientAsync, PixelClientKwargs
from ._sync import PixelClient
from .settings import PixelApiSettings

from .models import *  # noqa: F403

__version__ = version("pixel_client")


@overload
def get_client(
    async_: Literal[False] = ...,
    settings: PixelApiSettings | None = None,
    **kwargs: Unpack[PixelClientKwargs],
) -> PixelClient: ...


@overload
def get_client(
    async_: Literal[True] = ...,
    settings: PixelApiSettings | None = None,
    **kwargs: Unpack[PixelClientKwargs],
) -> PixelClientAsync: ...


def get_client(
    async_: bool = False,
    settings: PixelApiSettings | None = None,
    **kwargs: Unpack[PixelClientKwargs],
) -> PixelClientAsync | PixelClient:
    """
    Get the pixel client.

    Args:
        async_ (bool): Whether to return an asynchronous client.
        settings (PixelApiSettings | None): Settings for the Pixel API client. If None, defaults are used.
        **kwargs: Additional keyword arguments to pass to the client constructor.
    Returns:
        PixelClientAsync | PixelClient: An instance of the Pixel API client, either synchronous or asynchronous.

    Example:
        ```python
        from pixel_client import get_client, PixelApiSettings
        # Settings from environment variables
        async_client = get_client(async_=True)
        # Settings from a .env file, see https://docs.pydantic.dev/latest/concepts/pydantic_settings/#dotenv-env-support
        settings = PixelApiSettings(_env_file="path/to/.env")
        # async_ defaults to False, so this will return a synchronous client
        sync_client = get_client(settings=settings)
        ```

    Note:
        The client is cached and will be reused on subsequent calls, unless the settings change.
    """
    return _cached_get_client(async_, settings or PixelApiSettings(), **kwargs)  # type: ignore


@lru_cache
def _cached_get_client(
    async_: bool, settings: PixelApiSettings, **kwargs: Unpack[PixelClientKwargs]
) -> PixelClientAsync | PixelClient:
    async_client = PixelClientAsync.from_settings(settings, **kwargs)
    if async_:
        return async_client
    return PixelClient(async_client)

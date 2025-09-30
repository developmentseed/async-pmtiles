"""FileSystems for PMTiles Reader."""

import abc
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import aiofiles
import httpx

try:
    import aioboto3

except ImportError:  # pragma: nocover
    aioboto3 = None  # type: ignore

try:
    from gcloud.aio.storage import Storage as GcpStorage

except ImportError:  # pragma: nocover
    GcpStorage = None  # type: ignore


@dataclass
class FileSystem(abc.ABC):
    """Filesystem base class"""

    filepath: str
    ctx: AsyncExitStack = field(default_factory=AsyncExitStack, init=False)

    @abc.abstractmethod
    async def get(self, offset: int, length: int) -> bytes:
        """Perform a range request"""
        ...

    @abc.abstractmethod
    async def __aenter__(self):
        """Async context management"""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async context management"""
        await self.ctx.aclose()

    @classmethod
    def create_from_filepath(cls, filepath: str, **kwargs: Any) -> "FileSystem":
        """Instantiate the appropriate filesystem based on filepath scheme"""
        parsed = urlparse(filepath)

        if parsed.scheme in {"http", "https"}:
            return HttpFileSystem(filepath, **kwargs)

        elif parsed.scheme == "s3":
            return S3FileSystem(filepath, **kwargs)

        elif parsed.scheme == "gs":
            return GcsFileSystem(filepath, **kwargs)

        elif parsed.scheme == "file":
            return LocalFileSystem(filepath, **kwargs)

        # Invalid Scheme
        elif parsed.scheme:
            raise ValueError(f"'{parsed.scheme}' is not supported")

        # fallback to LocalFileSystem
        else:
            return LocalFileSystem(filepath, **kwargs)


@dataclass
class LocalFileSystem(FileSystem):
    """Local (disk) filesystem"""

    file: Any = field(init=False)

    async def get(self, offset: int, length: int) -> bytes:
        """Perform a range request"""
        await self.file.seek(offset)
        return await self.file.read(length + 1)

    async def __aenter__(self):
        """Async context management"""
        self.file = await self.ctx.enter_async_context(
            aiofiles.open(self.filepath, "rb")
        )
        return self


@dataclass
class HttpFileSystem(FileSystem):
    """HTTP filesystem"""

    client: httpx.AsyncClient = field(init=False)

    async def get(self, offset: int, length: int) -> bytes:
        """Perform a range request"""
        range_header = {"Range": f"bytes={offset}-{offset + length}"}
        resp = await self.client.get(self.filepath, headers=range_header)
        resp.raise_for_status()
        return resp.content

    async def __aenter__(self):
        """Async context management"""
        self.client = await self.ctx.enter_async_context(httpx.AsyncClient())
        return self


@dataclass
class S3FileSystem(FileSystem):
    """S3 filesystem"""

    request_payer: bool = False

    _session: Any = field(init=False)
    _resource: Any = field(init=False)
    _obj: Any = field(init=False)

    def __post_init__(self):
        """Check for dependency."""
        assert aioboto3 is not None, "'aioboto3' must be installed to use S3 FileSystem"

    async def get(self, offset: int, length: int) -> bytes:
        """Perform a range request"""
        kwargs = {}
        if self.request_payer:
            kwargs["RequestPayer"] = self.request_payer

        req = await self._obj.get(Range=f"bytes={offset}-{offset + length}", **kwargs)

        return await req["Body"].read()

    async def __aenter__(self):
        """Async context management"""
        parsed = urlparse(self.filepath)
        self._session = aioboto3.Session()
        self._resource = await self.ctx.enter_async_context(
            self._session.resource("s3")
        )
        self._obj = await self._resource.Object(parsed.netloc, parsed.path.strip("/"))
        return self


@dataclass
class GcsFileSystem(FileSystem):
    """GCS filesystem"""

    _client: GcpStorage = field(init=False)
    _bucket: str = field(init=False)
    _obj: str = field(init=False)

    def __post_init__(self):
        """Check for dependency."""
        assert (
            GcpStorage is not None
        ), "'gcloud-aio-storage' must be installed to use GCS FileSystem"

    async def get(self, offset: int, length: int) -> bytes:
        """Perform a range request"""
        headers = {"Range": f"bytes={offset}-{offset + length}"}
        return await self._client.download(self._bucket, self._obj, headers=headers)

    async def __aenter__(self):
        """Async context management"""
        parsed_path = urlparse(self.filepath)
        self._client = await self.ctx.enter_async_context(GcpStorage())
        self._bucket = parsed_path.netloc
        self._obj = parsed_path.path.strip("/")
        return self

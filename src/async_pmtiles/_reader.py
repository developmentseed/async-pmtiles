"""Async version of protomaps/PMTiles."""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, Self

from pmtiles.tile import (
    Compression,
    TileType,
    deserialize_directory,
    deserialize_header,
    find_tile,
    zxy_to_tileid,
)

if TYPE_CHECKING:
    import sys

    from pmtiles.tile import HeaderDict

    if sys.version_info >= (3, 12):
        from collections.abc import Buffer
    else:
        from typing_extensions import Buffer


class Store(Protocol):
    """A generic protocol for accessing byte ranges of files.

    This is compatible with [obspec.GetRangeAsync][obspec.GetRangeAsync] and is
    implemented by [obstore] stores, such as [S3Store][obstore.store.S3Store],
    [GCSStore][obstore.store.GCSStore], and [AzureStore][obstore.store.AzureStore].

    [obstore]: https://developmentseed.org/obstore/latest/
    """

    async def get_range_async(
        self,
        path: str,
        *,
        start: int,
        length: int,
    ) -> Buffer:
        """Asynchronously fetch a byte range from a file.

        Args:
            path: The path to the file within the store.
            start: The starting byte offset of the range to fetch.
            length: The length of the range to fetch.

        Returns:
            Byte buffer.

        """
        ...


@dataclass()
class PMTilesReader:
    """An asynchronous [PMTiles] Reader.

    [PMTiles]: https://docs.protomaps.com/
    """

    path: str
    """The path within the store to the PMTiles file."""

    store: Store
    """A reference to the store used for fetching byte ranges."""

    header: HeaderDict
    """The underlying raw PMTiles header metadata."""

    @classmethod
    async def open(cls, path: str, *, store: Store) -> Self:
        """Open a PMTiles file.

        Args:
            path: The path within the store to the PMTiles file.
            store: A generic "store" that implements fetching byte ranges
                asynchronously.

        Raises:
            ValueError: If the PMTiles version is unsupported.

        Returns:
            An instance of PMTilesReader.

        """
        header_values = await store.get_range_async(
            path,
            start=0,
            length=127,
        )
        spec_version = memoryview(header_values)[7]
        if spec_version != 3:  # noqa: PLR2004
            msg = f"Unsupported PMTiles spec version: {spec_version}"
            raise ValueError(msg)

        # https://github.com/protomaps/PMTiles/pull/638 allows passing a buffer directly
        header = deserialize_header(bytes(header_values))

        return cls(path=path, store=store, header=header)

    async def metadata(self) -> dict:
        """Load user-defined metadata stored in the PMTiles archive."""
        metadata = await self.store.get_range_async(
            self.path,
            start=self.header["metadata_offset"],
            length=self.header["metadata_length"],
        )
        match self.header["internal_compression"]:
            case Compression.NONE:
                metadata = bytes(metadata)
            case Compression.GZIP:
                metadata = gzip.decompress(metadata)
            case Compression.BROTLI:
                raise NotImplementedError("Brotli compression is not yet supported")
            case Compression.ZSTD:
                raise NotImplementedError("Zstd compression is not yet supported")
            case Compression.UNKNOWN:
                # What to do here? Maybe just warn?
                raise NotImplementedError("Unknown compression is not supported")
            case _:
                raise NotImplementedError

        return json.loads(metadata)

    async def get_tile(self, x: int, y: int, z: int) -> Buffer | None:
        """Load data for a specific tile given its x, y, and z coordinates.

        Note that no decompression is applied.
        """
        tile_id = zxy_to_tileid(z, x, y)

        dir_offset = self.header["root_offset"]
        dir_length = self.header["root_length"]
        for _ in range(4):  # max depth
            directory_values = await self.store.get_range_async(
                self.path,
                start=dir_offset,
                length=dir_length,
            )
            directory = deserialize_directory(directory_values)

            if result := find_tile(directory, tile_id):
                if result.run_length == 0:
                    dir_offset = self.header["leaf_directory_offset"] + result.offset
                    dir_length = result.length

                else:
                    return await self.store.get_range_async(
                        self.path,
                        start=self.header["tile_data_offset"] + result.offset,
                        length=result.length,
                    )

        return None

    @property
    def minzoom(self) -> int:
        """The minimum zoom of the archive."""
        return self.header["min_zoom"]

    @property
    def maxzoom(self) -> int:
        """The maximum zoom of the archive."""
        return self.header["max_zoom"]

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """The bounding box of the archive as (min_lon, min_lat, max_lon, max_lat)."""
        return (
            self.header["min_lon_e7"] / 10000000,
            self.header["min_lat_e7"] / 10000000,
            self.header["max_lon_e7"] / 10000000,
            self.header["max_lat_e7"] / 10000000,
        )

    @property
    def center(self) -> tuple[float, float, int]:
        """The center of the archive as (center_lon, center_lat, center_zoom)."""
        return (
            self.header["center_lon_e7"] / 10000000,
            self.header["center_lat_e7"] / 10000000,
            self.header["center_zoom"],
        )

    @property
    def tile_compression(self) -> Compression:
        """Return the compression type used for tiles."""
        return self.header["tile_compression"]

    @property
    def tile_type(self) -> TileType:
        """Return the type of tiles contained in the archive."""
        return self.header["tile_type"]

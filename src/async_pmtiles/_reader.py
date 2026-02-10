"""Async version of protomaps/PMTiles."""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

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

    from obspec import GetRangeAsync
    from pmtiles.tile import HeaderDict

    if sys.version_info >= (3, 12):
        from collections.abc import Buffer
    else:
        from typing_extensions import Buffer


@dataclass()
class PMTilesReader:
    """PMTiles Reader."""

    path: str
    store: GetRangeAsync
    header: HeaderDict

    @classmethod
    async def open(cls, path: str, store: GetRangeAsync) -> Self:
        """Open a PMTiles file."""
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
        """Return PMTiles Metadata."""
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
        """Get Tile Data."""
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
        """Return minzoom."""
        return self.header["min_zoom"]

    @property
    def maxzoom(self) -> int:
        """Return maxzoom."""
        return self.header["max_zoom"]

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Return Archive Bounds."""
        return (
            self.header["min_lon_e7"] / 10000000,
            self.header["min_lat_e7"] / 10000000,
            self.header["max_lon_e7"] / 10000000,
            self.header["max_lat_e7"] / 10000000,
        )

    @property
    def center(self) -> tuple[float, float, int]:
        """Return Archive center."""
        return (
            self.header["center_lon_e7"] / 10000000,
            self.header["center_lat_e7"] / 10000000,
            self.header["center_zoom"],
        )

    @property
    def is_vector(self) -> bool:
        """Return tile type."""
        return self.header["tile_type"] == TileType.MVT

    @property
    def tile_compression(self) -> Compression:
        """Return tile compression type."""
        return self.header["tile_compression"]

    @property
    def tile_type(self) -> TileType:
        """Return tile type."""
        return self.header["tile_type"]

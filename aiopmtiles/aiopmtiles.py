"""Async version of protomaps/PMTiles."""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from obspec import GetRangeAsync
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


@dataclass
class PMTilesReader:
    """PMTiles Reader."""

    path: str
    store: GetRangeAsync

    header: HeaderDict = field(init=False)
    _header_offset: int = field(default=0, init=False)
    _header_length: int = field(default=127, init=False)

    async def __aenter__(self):
        """Support using with Context Managers."""

        header_values = await self.store.get_range_async(
            self.path,
            start=self._header_offset,
            length=self._header_length,
        )
        spec_version = memoryview(header_values)[7]
        assert spec_version == 3, "Only Version 3 of PMTiles specification is supported"

        self.header = deserialize_header(memoryview(header_values))

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Support using with Context Managers."""
        pass

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
                # TODO: what to do here? Maybe just warn?
                raise NotImplementedError("Unknown compression is not supported")
            case _:
                raise NotImplementedError()

        return json.loads(metadata)

    async def get_tile(self, z, x, y) -> Buffer | None:
        """Get Tile Data."""
        tile_id = zxy_to_tileid(z, x, y)

        dir_offset = self.header["root_offset"]
        dir_length = self.header["root_length"]
        for _ in range(0, 4):  # max depth
            directory_values = await self.store.get_range_async(
                self.path, start=dir_offset, length=dir_length
            )
            directory = deserialize_directory(directory_values)

            if result := find_tile(directory, tile_id):
                if result.run_length == 0:
                    dir_offset = self.header["leaf_directory_offset"] + result.offset
                    dir_length = result.length

                else:
                    data = await self.store.get_range_async(
                        self.path,
                        start=self.header["tile_data_offset"] + result.offset,
                        length=result.length,
                    )
                    return data

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

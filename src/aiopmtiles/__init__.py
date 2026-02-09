"""async-pmtiles: asynchronous interface for reading PMTiles files."""

__version__ = "0.1.0"

from .aiopmtiles import PMTilesReader

__all__ = ["PMTilesReader"]

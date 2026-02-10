"""Test PMTilesReader."""

from pathlib import Path

import pytest
from obstore.store import LocalStore

from async_pmtiles import PMTilesReader

FIXTURES_DIR = Path(__file__).parent / "fixtures"
VECTOR_PMTILES = "protomaps(vector)ODbL_firenze.pmtiles"
RASTER_PMTILES = "usgs-mt-whitney-8-15-webp-512.pmtiles"
V2_PMTILES = "stamen_toner(raster)CC-BY+ODbL_z3.pmtiles"


@pytest.mark.asyncio
async def test_reader_vector():
    """Test PMTilesReader with Vector PMTiles."""
    store = LocalStore(FIXTURES_DIR)

    src = await PMTilesReader.open(VECTOR_PMTILES, store=store)
    assert src.header
    assert src.bounds == (11.154026, 43.7270125, 11.3289395, 43.8325455)
    assert src.minzoom == 0
    assert src.maxzoom == 14
    assert src.center[2] == 0
    assert src.is_vector
    assert src.tile_compression.name == "GZIP"

    assert src.tile_type.name == "MVT"

    metadata = await src.metadata()
    assert "attribution" in metadata
    assert "tilestats" in metadata


@pytest.mark.asyncio
async def test_reader_raster():
    """Test PMTilesReader with raster PMTiles."""
    store = LocalStore(FIXTURES_DIR)

    src = await PMTilesReader.open(RASTER_PMTILES, store=store)
    assert src.header
    assert src.bounds == (-118.31982, 36.56109, -118.26069, 36.59301)
    assert src.minzoom == 8
    assert src.maxzoom == 15
    assert src.center[2] == 12
    assert not src.is_vector
    assert src.tile_compression.name == "NONE"

    assert src.tile_type.name == "WEBP"

    metadata = await src.metadata()
    assert "attribution" in metadata
    assert "type" in metadata


@pytest.mark.asyncio
async def test_reader_bad_spec():
    """Should raise an error if not spec == 3."""
    store = LocalStore(FIXTURES_DIR)

    with pytest.raises(ValueError, match="Unsupported PMTiles spec version"):
        await PMTilesReader.open(V2_PMTILES, store=store)

"""test IO FileSystem."""

import os

import pytest

from aiopmtiles.io import (
    FileSystem,
    GcsFileSystem,
    HttpFileSystem,
    LocalFileSystem,
    S3FileSystem,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VECTOR_PMTILES = os.path.join(FIXTURES_DIR, "protomaps(vector)ODbL_firenze.pmtiles")


@pytest.mark.parametrize(
    "url,fs",
    [
        ("myfile.pmtiles", LocalFileSystem),
        ("file:///myfile.pmtiles", LocalFileSystem),
        ("s3://bucket/myfile.pmtiles", S3FileSystem),
        ("gs://bucket/myfile.pmtiles", GcsFileSystem),
        ("http://url.io/myfile.pmtiles", HttpFileSystem),
        ("https://url.io/myfile.pmtiles", HttpFileSystem),
    ],
)
def test_create_from_filepath(url, fs):
    """Test Filesystem creation from url."""
    assert isinstance(FileSystem.create_from_filepath(url), fs)


def test_bad_schema():
    """Should raise ValueError."""
    with pytest.raises(ValueError):
        FileSystem.create_from_filepath("something://myfile.pmtiles")


@pytest.mark.asyncio
async def test_local_fs():
    """Test LocalFilesSytem."""
    async with LocalFileSystem(VECTOR_PMTILES) as fs:
        assert not fs.file.closed
        magic_bytes = await fs.get(0, 6)
        assert magic_bytes.decode() == "PMTiles"
    assert fs.file.closed

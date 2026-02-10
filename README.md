# async-pmtiles

An asynchronous [PMTiles] reader for Python.

The [PMTiles format] is a cloud-native, compressed, single-file archive for storing tiled vector and raster map data.

[PMTiles]: https://docs.protomaps.com/
[PMTiles format]: https://docs.protomaps.com/pmtiles/

**Documentation**: <https://developmentseed.org/async-pmtiles/>

## Install

```
pip install async-pmtiles
```

## Example

```python
from async_pmtiles import PMTilesReader
from obstore.store import HTTPStore

store = HTTPStore("https://r2-public.protomaps.com/protomaps-sample-datasets")
src = await PMTilesReader.open("cb_2018_us_zcta510_500k.pmtiles", store=store)

# PMTiles Metadata
meta = await src.metadata()

# Spatial Metadata
bounds = src.bounds
minzoom, maxzoom = src.minzoom, src.maxzoom

# Is the data a Vector Tile Archive
assert src.is_vector

# PMTiles tiles type
src.tile_type

# Tile Compression
src.tile_compression

# Get Tile
data = await src.get_tile(x=0, y=0, z=0)
```

### Custom Client

Here's an example with using a small wrapper around `aiohttp` to read from arbitrary URLs:

```py
@dataclass
class AiohttpAdapter(GetRangeAsync):
    session: ClientSession

    async def get_range_async(
        self,
        path: str,
        *,
        start: int,
        length: int,
    ) -> Buffer:
        inclusive_end = start + length - 1
        headers = {"Range": f"bytes={start}-{inclusive_end}"}
        async with self.session.get(path, headers=headers) as response:
            return await response.read()


async with ClientSession() as session:
    store = AiohttpAdapter(session)
    url = "https://r2-public.protomaps.com/protomaps-sample-datasets/cb_2018_us_zcta510_500k.pmtiles"
    src = await PMTilesReader.open(url, store=store)

    assert src.header
    assert src.bounds == (-176.684714, -14.37374, 145.830418, 71.341223)
    assert src.minzoom == 0
    assert src.maxzoom == 7
    assert src.tile_compression == Compression.GZIP
    assert src.tile_type == TileType.MVT
```

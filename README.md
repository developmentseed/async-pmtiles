# aiopmtiles

<p align="center">
  <em>Async Version of Python PMTiles Reader.</em>
</p>
<p align="center">
  <a href="https://github.com/developmentseed/aiopmtiles/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/developmentseed/aiopmtiles/workflows/CI/badge.svg" alt="Test">
  </a>
  <a href="https://codecov.io/gh/developmentseed/aiopmtiles" target="_blank">
      <img src="https://codecov.io/gh/developmentseed/aiopmtiles/branch/main/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://pypi.org/project/aiopmtiles" target="_blank">
      <img src="https://img.shields.io/pypi/v/aiopmtiles?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>
  <a href="https://pypistats.org/packages/aiopmtiles" target="_blank">
      <img src="https://img.shields.io/pypi/dm/aiopmtiles.svg" alt="Downloads">
  </a>
  <a href="https://github.com/developmentseed/aiopmtiles/blob/main/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/developmentseed/aiopmtiles.svg" alt="Downloads">
  </a>
</p>

---

**Documentation**: <a href="https://developmentseed.org/aiopmtiles/" target="_blank">https://developmentseed.org/aiopmtiles/</a>

**Source Code**: <a href="https://github.com/developmentseed/aiopmtiles" target="_blank">https://github.com/developmentseed/aiopmtiles</a>

---

`aiopmtiles` is a python `Async I/O` version of the great [PMTiles](https://github.com/protomaps/PMTiles) python reader.

The [**PMTiles**](https://github.com/protomaps/PMTiles) format is a *Cloud-optimized + compressed single-file tile archives for vector and raster maps*.

## Installation

```bash
$ python -m pip install pip -U

# From Pypi
$ python -m pip install aiopmtiles

# Or from source
$ python -m pip install git+http://github.com/developmentseed/aiopmtiles
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

## Contribution & Development

See [CONTRIBUTING.md](https://github.com/developmentseed/aiopmtiles/blob/main/CONTRIBUTING.md)

## Authors

See [contributors](https://github.com/developmentseed/aiopmtiles/graphs/contributors)

## Changes

See [CHANGES.md](https://github.com/developmentseed/aiopmtiles/blob/main/CHANGES.md).

## License

See [LICENSE](https://github.com/developmentseed/aiopmtiles/blob/main/LICENSE)

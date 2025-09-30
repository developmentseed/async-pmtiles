Create a simple FastAPI application to serve tiles from PMTiles

```python
from typing import Dict

from fastapi import FastAPI, Path, Query
from pmtiles.tile import Compression
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from aiopmtiles import Reader


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/metadata")
async def metadata(url: str = Query(..., description="PMTiles archive URL.")):
    """get Metadata."""
    async with Reader(url) as src:
        return await src.metadata()

@app.get("/tiles/{z}/{x}/{y}", response_class=Response)
async def tiles(
    z: int = Path(ge=0, le=30, description="TMS tiles's zoom level"),
    x: int = Path(description="TMS tiles's column"),
    y: int = Path(description="TMS tiles's row"),
    url: str = Query(..., description="PMTiles archive URL."),
):
    """get Tile."""
    headers: Dict[str, str] = {}

    async with Reader(url) as src:
        data = await src.get_tile(z, x, y)
        if src.header["internal_compression"] == Compression.GZIP:
            headers["Content-Encoding"] = "gzip"

    return Response(data, media_type="application/x-protobuf", headers=headers)

@app.get("/tilejson.json")
async def tilejson(
    request: Request,
    url: str = Query(..., description="PMTiles archive URL."),
):
    """get TileJSON."""
    async with Reader(url) as src:
        tilejson = {
            "tilejson": "3.0.0",
            "name": "pmtiles",
            "version": "1.0.0",
            "scheme": "xyz",
            "tiles": [
                str(request.url_for("tiles", z="{z}", x="{x}", y="{y}")) + f"?url={url}"
            ],
            "minzoom": src.minzoom,
            "maxzoom": src.maxzoom,
            "bounds": src.bounds,
            "center": src.center,
        }

        # If Vector Tiles then we can try to add more metadata
        if src.is_vector:
            if vector_layers := meta.get("vector_layers"):
                tilejson["vector_layers"] = vector_layers

    return tilejson


@app.get("/style.json")
async def stylejson(
    request: Request,
    url: str = Query(..., description="PMTiles archive URL."),
):
    """get StyleJSON."""
    tiles_url = str(request.url_for("tiles", z="{z}", x="{x}", y="{y}")) + f"?url={url}"

    async with Reader(url) as src:
        if src.is_vector:
            style_json = {
                "version": 8,
                "sources": {
                    "pmtiles": {
                        "type": "vector",
                        "scheme": "xyz",
                        "tiles": [tiles_url],
                        "minzoom": src.minzoom,
                        "maxzoom": src.maxzoom,
                        "bounds": src.bounds,
                    },
                },
                "layers": [],
                "center": [src.center[0], src.center[1]],
                "zoom": src.center[2],
            }

            meta = await src.metadata()
            if vector_layers := meta.get("vector_layers"):
                for layer in vector_layers:
                    layer_id = layer["id"]
                    if layer_id == "mask":
                        style_json["layers"].append(
                            {
                                "id": f"{layer_id}_fill",
                                "type": "fill",
                                "source": "pmtiles",
                                "source-layer": layer_id,
                                "filter": ["==", ["geometry-type"], "Polygon"],
                                "paint": {
                                    'fill-color': 'black',
                                    'fill-opacity': 0.8
                                },
                            }
                        )

                    else:
                        style_json["layers"].append(
                            {
                                "id": f"{layer_id}_fill",
                                "type": "fill",
                                "source": "pmtiles",
                                "source-layer": layer_id,
                                "filter": ["==", ["geometry-type"], "Polygon"],
                                "paint": {
                                    'fill-color': 'rgba(200, 100, 240, 0.4)',
                                    'fill-outline-color': '#000'
                                },
                            }
                        )

                    style_json["layers"].append(
                        {
                            "id": f"{layer_id}_stroke",
                            "source": 'pmtiles',
                            "source-layer": layer_id,
                            "type": 'line',
                            "filter": ["==", ["geometry-type"], "LineString"],
                            "paint": {
                                'line-color': '#000',
                                'line-width': 1,
                                'line-opacity': 0.75
                            }
                        }
                    )
                    style_json["layers"].append(
                        {
                            "id": f"{layer_id}_point",
                            "source": 'pmtiles',
                            "source-layer": layer_id,
                            "type": 'circle',
                            "filter": ["==", ["geometry-type"], "Point"],
                            "paint": {
                                'circle-color': '#000',
                                'circle-radius': 2.5,
                                'circle-opacity': 0.75
                            }
                        }
                    )

        else:
            style_json = {
                "sources": {
                    "pmtiles": {
                        "type": "raster",
                        "scheme": "xyz",
                        "tiles": [tiles_url],
                        "minzoom": src.minzoom,
                        "maxzoom": src.maxzoom,
                        "bounds": src.bounds,
                    },
                },
                "layers": [
                    {
                        "id": "raster",
                        "type": "raster",
                        "source": "pmtiles",
                    },
                ],
                "center": [src.center[0], src.center[1]],
                "zoom": src.center[2],
            }

    return style_json
```

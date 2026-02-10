# Contributing

Issues and pull requests are more than welcome.

First install `uv`. Then set up with:

```bash
git clone https://github.com/developmentseed/async-pmtiles
cd async-pmtiles
uv sync
```

## Running tests

```sh
uv run pytest
```

## Documentation

### Building locally

```
uv run --group docs mkdocs serve
```

### Publishing docs

Documentation is automatically published when a new tag with `v*` is pushed to `main`. Alternatively, you can manually publish docs by triggering the docs publish workflow from the GitHub actions UI.

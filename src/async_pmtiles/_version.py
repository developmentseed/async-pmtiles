from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("async-pmtiles")
except PackageNotFoundError:
    __version__ = "uninstalled"

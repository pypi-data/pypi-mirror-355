from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("who-cares")
except PackageNotFoundError:
    __version__ = "unknown"

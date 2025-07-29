from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("geff")
except PackageNotFoundError:
    __version__ = "uninstalled"

try:
    import networkx
except ImportError as err:
    raise ImportError(
        "The networkx submodule depends on networkx as an optional dependency. "
        "Please run `pip install geff[networkx]` to install the optional dependency."
    ) from err

from .io import read, write

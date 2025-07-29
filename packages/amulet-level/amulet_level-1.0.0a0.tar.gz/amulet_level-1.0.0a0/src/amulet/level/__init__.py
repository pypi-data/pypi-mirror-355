import logging

from . import _version

__version__ = _version.get_versions()["version"]

# init a default logger
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def _init() -> None:
    import os
    import sys
    import ctypes

    if sys.platform == "win32":
        lib_path = os.path.join(os.path.dirname(__file__), "amulet_level.dll")
    elif sys.platform == "darwin":
        lib_path = os.path.join(os.path.dirname(__file__), "libamulet_level.dylib")
    elif sys.platform == "linux":
        lib_path = os.path.join(os.path.dirname(__file__), "libamulet_level.so")
    else:
        raise RuntimeError(f"Unsupported platform {sys.platform}")

    # Import dependencies
    import amulet.game
    import amulet.utils
    import amulet.leveldb
    import amulet.anvil

    # Load the shared library
    ctypes.cdll.LoadLibrary(lib_path)

    from ._amulet_level import init

    init(sys.modules[__name__])


_init()

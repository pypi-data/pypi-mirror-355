from .docrpy import *

__doc__ = docrpy.__doc__
if hasattr(docrpy, "__all__"):
    __all__ = docrpy.__all__
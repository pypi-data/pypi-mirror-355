"""Singleton Base Class to make any other class a singleton with proper type hinting."""

__version__ = "1.0.5"

import sys

if sys.version_info < (3, 11):
    from .singleton_base_legacy import SingletonBase
else:
    from .singleton_base_new import SingletonBase


__all__ = ["SingletonBase", "__version__"]

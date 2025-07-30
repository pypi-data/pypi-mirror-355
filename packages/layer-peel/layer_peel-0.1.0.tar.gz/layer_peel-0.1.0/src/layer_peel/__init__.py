"""
Layer Peel - Python library for recursively extracting multi-layer nested compressed files

This library provides a simple yet powerful API for handling nested compressed files,
supporting recursive extraction of various formats including ZIP, TAR, 7Z, RAR, etc.
"""

__version__ = "0.1.0"
__author__ = "Lacia Project"

from .iter_unpack import extract
from .utils import get_mime_type, fix_encoding, read_stream
from .types import RawIOBase

__all__ = [
    "extract",
    "get_mime_type",
    "fix_encoding",
    "read_stream",
    "RawIOBase",
    "__version__",
]

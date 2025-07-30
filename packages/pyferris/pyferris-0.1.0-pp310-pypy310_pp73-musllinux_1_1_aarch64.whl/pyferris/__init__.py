"""
PyFerris - High-performance parallel processing library for Python, powered by Rust and PyO3.
"""

__version__ = "0.1.0"
from .core import parallel_map, parallel_reduce, parallel_filter, parallel_starmap
from .config import Config, get_chunk_size, get_worker_count, set_chunk_size, set_worker_count
from .executor import Executor
from .io import csv, file_reader, simple_io, file_writer, json, parallel_io

__all__ = [
    # core base functionality
    "__version__",
    "parallel_map",
    "parallel_reduce",
    "parallel_filter",
    "parallel_starmap",

    # configuration management
    "Config",
    "get_chunk_size",
    "get_worker_count",
    "set_chunk_size",
    "set_worker_count",

    # executor
    "Executor",

    # I/O operations
    "csv",
    "file_reader",
    "simple_io",
    "file_writer",
    "json",
    "parallel_io"
]
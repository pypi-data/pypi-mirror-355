"""
Sortium
=======

Sortium is a utility library for sorting and organizing files on disk.

It provides:

- The `Sorter` class for sorting files by type and modification date.
- Utility functions for working with the file system:
  - `get_file_modified_date`
  - `get_subdirectories_names`
  - `flatten_dir`

Example usage::

    from sortium import Sorter
    sorter = Sorter()
    sorter.sort_by_type("/path/to/folder")
    sorter.sort_by_date("/path/to/folder", ["Images", "Documents"])
"""

from .sorter import Sorter

__all__ = [
    "Sorter",
]

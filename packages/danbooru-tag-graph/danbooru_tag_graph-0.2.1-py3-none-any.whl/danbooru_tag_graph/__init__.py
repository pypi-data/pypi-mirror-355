"""
Danbooru Tag Graph

A NetworkX-based graph system for efficiently managing Danbooru tag relationships
including implications, aliases, and deprecated status.
"""

__version__ = "0.2.1"

from .danbooru_tag_graph import DanbooruTagGraph

__all__ = ["DanbooruTagGraph"] 
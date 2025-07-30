"""
Core modules for DataLineagePy.

This module contains the fundamental classes and functionality for data lineage tracking.
"""

try:
    from .tracker import LineageTracker
    from .nodes import DataNode, FileNode, DatabaseNode
    from .edges import LineageEdge
    from .dataframe_wrapper import LineageDataFrame
    from .operations import Operation
except ImportError:
    # Modules will be created as needed
    pass

__all__ = [
    'LineageTracker',
    'DataNode', 'FileNode', 'DatabaseNode',
    'LineageEdge',
    'LineageDataFrame',
    'Operation',
]

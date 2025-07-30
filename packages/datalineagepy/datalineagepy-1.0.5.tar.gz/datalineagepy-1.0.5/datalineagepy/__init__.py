"""
DataLineagePy - A comprehensive Python library for tracking and visualizing data lineage.

This library provides automatic lineage tracking for pandas and PySpark workflows,
with support for various data sources including databases, files, and cloud storage.
"""

__version__ = "1.0.5"
__author__ = "Arbaznazir"
__email__ = "arbaznazir4@gmail.com"

# Core imports
try:
    from .core.tracker import LineageTracker
    from .core.nodes import DataNode, FileNode, DatabaseNode
    from .core.edges import LineageEdge
    from .core.dataframe_wrapper import LineageDataFrame
    from .core.operations import Operation
except ImportError:
    # Graceful fallback if core modules aren't available yet
    pass

# Connector imports
try:
    from .connectors.database import DatabaseConnector
    from .connectors.file import FileConnector
    from .connectors.cloud import CloudStorageConnector
except ImportError:
    pass

# Visualization imports
try:
    from .visualization.graph_visualizer import GraphVisualizer
    from .visualization.report_generator import ReportGenerator
except ImportError:
    pass

# Testing imports
try:
    from .testing.validators import LineageValidator
    from .testing.benchmarks import BenchmarkSuite
except ImportError:
    pass

__all__ = [
    'LineageTracker',
    'DataNode', 'FileNode', 'DatabaseNode',
    'LineageEdge',
    'LineageDataFrame',
    'Operation',
    'DatabaseConnector',
    'FileConnector',
    'CloudStorageConnector',
    'GraphVisualizer',
    'ReportGenerator',
    'LineageValidator',
    'BenchmarkSuite',
]

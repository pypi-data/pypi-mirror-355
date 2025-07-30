"""
Native Apache Spark integration for DataLineagePy.

This module provides:
- LineageSparkDataFrame wrapper for PySpark DataFrames
- Automatic lineage tracking for Spark operations
- Spark SQL lineage extraction
- Distributed lineage collection
- Integration with Spark Catalyst optimizer
"""

from .lineage_spark_dataframe import LineageSparkDataFrame
from .spark_tracker import SparkLineageTracker
from .sql_parser import SparkSQLParser
from .catalyst_integration import CatalystLineageExtractor

__all__ = [
    'LineageSparkDataFrame',
    'SparkLineageTracker',
    'SparkSQLParser',
    'CatalystLineageExtractor',
]

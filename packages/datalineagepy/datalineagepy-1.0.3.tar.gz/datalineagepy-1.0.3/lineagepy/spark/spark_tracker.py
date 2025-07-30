"""
Spark-specific lineage tracker for advanced Spark integration.
"""

import logging
from typing import Dict, List, Any, Optional
from ..core.tracker import LineageTracker
from ..core.data_structures import TransformationType

logger = logging.getLogger(__name__)

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.utils import AnalysisException
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False


class SparkLineageTracker:
    """
    Enhanced lineage tracker for Spark applications.
    """

    def __init__(self, spark_session: Optional['SparkSession'] = None):
        """
        Initialize Spark lineage tracker.

        Args:
            spark_session: Optional Spark session
        """
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark is required for Spark lineage tracking")

        self.spark = spark_session or SparkSession.getActiveSession()
        if self.spark is None:
            raise ValueError("No active Spark session found")

        self.lineage_tracker = LineageTracker()
        self._setup_spark_hooks()

    def _setup_spark_hooks(self) -> None:
        """Setup Spark execution hooks for automatic lineage capture."""
        try:
            # Register Spark listener for query execution
            from .spark_listener import LineageSparkListener
            listener = LineageSparkListener(self.lineage_tracker)
            self.spark.sparkContext.addSparkListener(listener)
            logger.info("Spark lineage listener registered")
        except ImportError:
            logger.warning("Spark listener not available")
        except Exception as e:
            logger.error(f"Failed to setup Spark hooks: {str(e)}")

    def track_sql_query(self, sql: str, result_table: str = None) -> Dict[str, Any]:
        """
        Track lineage for a Spark SQL query.

        Args:
            sql: SQL query string
            result_table: Optional name for result table

        Returns:
            Lineage information
        """
        try:
            # Parse the SQL query for lineage information
            from .sql_parser import SparkSQLParser
            parser = SparkSQLParser()
            lineage_info = parser.parse_query(sql)

            # Execute the query to get the plan
            df = self.spark.sql(sql)

            # Extract lineage from execution plan
            plan_lineage = self._extract_plan_lineage(
                df.queryExecution.analyzed)

            # Combine parser and plan lineage
            combined_lineage = self._combine_lineage_info(
                lineage_info, plan_lineage)

            # Track in lineage tracker
            self._track_sql_lineage(combined_lineage, result_table)

            return combined_lineage

        except Exception as e:
            logger.error(f"Failed to track SQL query: {str(e)}")
            return {}

    def _extract_plan_lineage(self, logical_plan) -> Dict[str, Any]:
        """
        Extract lineage information from Spark logical plan.

        Args:
            logical_plan: Spark logical plan

        Returns:
            Lineage information
        """
        try:
            from .catalyst_integration import CatalystLineageExtractor
            extractor = CatalystLineageExtractor()
            return extractor.extract_lineage(logical_plan)
        except ImportError:
            logger.warning("Catalyst integration not available")
            return {}
        except Exception as e:
            logger.error(f"Failed to extract plan lineage: {str(e)}")
            return {}

    def _combine_lineage_info(self, parser_info: Dict[str, Any],
                              plan_info: Dict[str, Any]) -> Dict[str, Any]:
        """Combine lineage information from different sources."""
        combined = parser_info.copy()

        # Merge plan information
        if 'tables' in plan_info:
            combined.setdefault('tables', []).extend(plan_info['tables'])

        if 'columns' in plan_info:
            combined.setdefault('columns', {}).update(plan_info['columns'])

        if 'operations' in plan_info:
            combined.setdefault('operations', []).extend(
                plan_info['operations'])

        return combined

    def _track_sql_lineage(self, lineage_info: Dict[str, Any],
                           result_table: Optional[str] = None) -> None:
        """Track SQL lineage in the lineage tracker."""
        try:
            # Create nodes for tables and columns
            for table_info in lineage_info.get('tables', []):
                # Implementation would create table and column nodes
                pass

            # Create edges for transformations
            for operation in lineage_info.get('operations', []):
                # Implementation would create transformation edges
                pass

        except Exception as e:
            logger.error(f"Failed to track SQL lineage: {str(e)}")

    def track_dataframe_write(self, df, path: str, format: str = 'parquet',
                              mode: str = 'overwrite', **options) -> None:
        """
        Track DataFrame write operations.

        Args:
            df: DataFrame to write
            path: Output path
            format: Output format
            mode: Write mode
            **options: Additional write options
        """
        try:
            from .lineage_spark_dataframe import LineageSparkDataFrame

            if isinstance(df, LineageSparkDataFrame):
                # Track the write operation
                context = {
                    'operation': 'write',
                    'path': path,
                    'format': format,
                    'mode': mode,
                    'options': options
                }

                # Create output table node
                output_table_id = f"output_{path.replace('/', '_')}"

                self.lineage_tracker.add_edge(
                    source_id=df.table_node.id,
                    target_id=output_table_id,
                    transformation_type=TransformationType.SPARK_WRITE,
                    context=context
                )

                logger.info(
                    f"Tracked write operation: {df.table_name} -> {path}")

        except Exception as e:
            logger.error(f"Failed to track DataFrame write: {str(e)}")

    def track_dataframe_read(self, path: str, format: str = 'parquet',
                             **options) -> Dict[str, Any]:
        """
        Track DataFrame read operations.

        Args:
            path: Input path
            format: Input format
            **options: Additional read options

        Returns:
            Read tracking information
        """
        try:
            # Create input table node
            input_table_id = f"input_{path.replace('/', '_')}"

            context = {
                'operation': 'read',
                'path': path,
                'format': format,
                'options': options
            }

            # Read the DataFrame to get schema
            df = self.spark.read.format(format).options(**options).load(path)

            # Create LineageSparkDataFrame
            from .lineage_spark_dataframe import LineageSparkDataFrame
            lineage_df = LineageSparkDataFrame(df, table_name=input_table_id)

            logger.info(
                f"Tracked read operation: {path} -> {lineage_df.table_name}")

            return {
                'dataframe': lineage_df,
                'table_id': input_table_id,
                'context': context
            }

        except Exception as e:
            logger.error(f"Failed to track DataFrame read: {str(e)}")
            return {}

    def get_query_lineage(self, query_id: str) -> Dict[str, Any]:
        """
        Get lineage information for a specific query.

        Args:
            query_id: Query identifier

        Returns:
            Query lineage information
        """
        try:
            # Implementation would retrieve query-specific lineage
            return self.lineage_tracker.get_lineage_summary()
        except Exception as e:
            logger.error(f"Failed to get query lineage: {str(e)}")
            return {}

    def export_spark_lineage(self, format: str = 'json') -> str:
        """
        Export Spark lineage in specified format.

        Args:
            format: Export format ('json', 'graphml', 'dot')

        Returns:
            Exported lineage data
        """
        try:
            if format == 'json':
                from ..visualization.exporters import LineageExporter
                exporter = LineageExporter(self.lineage_tracker)
                return exporter.export_json()
            else:
                logger.warning(f"Unsupported export format: {format}")
                return ""
        except Exception as e:
            logger.error(f"Failed to export Spark lineage: {str(e)}")
            return ""

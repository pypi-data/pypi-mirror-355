"""
LineageSparkDataFrame wrapper for Apache Spark integration.
"""

import inspect
from typing import Any, List, Optional, Dict, Union
from functools import wraps
import logging

from ..core.tracker import LineageTracker
from ..core.data_structures import TableNode, ColumnNode, TransformationType
from ..utils.context_capture import capture_context

logger = logging.getLogger(__name__)

try:
    from pyspark.sql import DataFrame as SparkDataFrame, SparkSession
    from pyspark.sql.functions import col
    from pyspark.sql.types import StructType
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    logger.warning(
        "PySpark not available. Spark integration will be disabled.")


class LineageSparkDataFrame:
    """
    Wrapper around PySpark DataFrame that automatically tracks lineage.
    """

    def __init__(self, spark_df: 'SparkDataFrame', table_name: Optional[str] = None,
                 parent_nodes: Optional[List[str]] = None):
        """
        Initialize LineageSparkDataFrame.

        Args:
            spark_df: PySpark DataFrame to wrap
            table_name: Optional table name for lineage tracking
            parent_nodes: Optional list of parent node IDs
        """
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark is required for Spark integration")

        self._spark_df = spark_df
        self._tracker = LineageTracker()

        # Generate table name if not provided
        if table_name is None:
            table_name = f"spark_table_{id(self)}"

        self.table_name = table_name
        self.parent_nodes = parent_nodes or []

        # Create table node
        self.table_node = TableNode(
            id=f"table_{self.table_name}",
            name=self.table_name,
            schema=self._extract_schema(),
            metadata={
                'type': 'spark_dataframe',
                'num_partitions': spark_df.rdd.getNumPartitions(),
                'is_cached': spark_df.is_cached,
                'storage_level': str(spark_df.storageLevel) if hasattr(spark_df, 'storageLevel') else None
            }
        )

        # Track table node
        self._tracker.add_node(self.table_node)

        # Create column nodes
        self._create_column_nodes()

        # Track parent relationships
        self._track_parent_relationships()

    def _extract_schema(self) -> Dict[str, str]:
        """Extract schema information from Spark DataFrame."""
        schema = {}
        try:
            for field in self._spark_df.schema.fields:
                schema[field.name] = str(field.dataType)
        except Exception as e:
            logger.error(f"Failed to extract schema: {str(e)}")
        return schema

    def _create_column_nodes(self) -> None:
        """Create column nodes for all columns in the DataFrame."""
        self.column_nodes = {}

        try:
            for field in self._spark_df.schema.fields:
                column_node = ColumnNode(
                    id=f"column_{self.table_name}_{field.name}",
                    name=field.name,
                    table_id=self.table_node.id,
                    data_type=str(field.dataType),
                    metadata={
                        'nullable': field.nullable,
                        'spark_type': str(field.dataType)
                    }
                )
                self.column_nodes[field.name] = column_node
                self._tracker.add_node(column_node)
        except Exception as e:
            logger.error(f"Failed to create column nodes: {str(e)}")

    def _track_parent_relationships(self) -> None:
        """Track relationships with parent nodes."""
        context = capture_context()

        for parent_node_id in self.parent_nodes:
            self._tracker.add_edge(
                source_id=parent_node_id,
                target_id=self.table_node.id,
                transformation_type=TransformationType.SPARK_OPERATION,
                context=context
            )

    def _track_operation(self, operation_name: str, target_df: 'LineageSparkDataFrame',
                         column_mappings: Optional[Dict[str, List[str]]] = None) -> None:
        """
        Track a Spark operation.

        Args:
            operation_name: Name of the operation
            target_df: Target DataFrame
            column_mappings: Optional column mappings
        """
        context = capture_context()
        context['operation'] = operation_name

        # Add table-level edge
        self._tracker.add_edge(
            source_id=self.table_node.id,
            target_id=target_df.table_node.id,
            transformation_type=TransformationType.SPARK_OPERATION,
            context=context
        )

        # Add column-level edges if mappings provided
        if column_mappings:
            for target_col, source_cols in column_mappings.items():
                if target_col in target_df.column_nodes:
                    target_col_id = target_df.column_nodes[target_col].id

                    for source_col in source_cols:
                        if source_col in self.column_nodes:
                            source_col_id = self.column_nodes[source_col].id

                            self._tracker.add_column_edge(
                                source_column_id=source_col_id,
                                target_column_id=target_col_id,
                                transformation_type=TransformationType.SPARK_OPERATION,
                                context=context
                            )

    # Core DataFrame operations
    def select(self, *cols) -> 'LineageSparkDataFrame':
        """Select columns with lineage tracking."""
        try:
            # Perform Spark operation
            result_df = self._spark_df.select(*cols)

            # Create lineage wrapper
            target_table_name = f"{self.table_name}_select"
            target_df = LineageSparkDataFrame(
                result_df,
                table_name=target_table_name,
                parent_nodes=[self.table_node.id]
            )

            # Track column mappings
            column_mappings = {}
            for col_expr in cols:
                if hasattr(col_expr, '_jc'):  # Column object
                    col_name = str(col_expr).replace(
                        'Column<', '').replace('>', '').strip("'\"")
                    if col_name in self.column_nodes:
                        column_mappings[col_name] = [col_name]
                elif isinstance(col_expr, str):  # String column name
                    if col_expr in self.column_nodes:
                        column_mappings[col_expr] = [col_expr]

            self._track_operation("select", target_df, column_mappings)

            return target_df

        except Exception as e:
            logger.error(f"Error in select operation: {str(e)}")
            # Return wrapper without lineage tracking on error
            return LineageSparkDataFrame(self._spark_df.select(*cols))

    def filter(self, condition) -> 'LineageSparkDataFrame':
        """Filter DataFrame with lineage tracking."""
        try:
            result_df = self._spark_df.filter(condition)

            target_table_name = f"{self.table_name}_filter"
            target_df = LineageSparkDataFrame(
                result_df,
                table_name=target_table_name,
                parent_nodes=[self.table_node.id]
            )

            # All columns pass through in filter
            column_mappings = {col: [col] for col in self.column_nodes.keys()}

            self._track_operation("filter", target_df, column_mappings)

            return target_df

        except Exception as e:
            logger.error(f"Error in filter operation: {str(e)}")
            return LineageSparkDataFrame(self._spark_df.filter(condition))

    def groupBy(self, *cols) -> 'LineageSparkGroupedData':
        """Group DataFrame with lineage tracking."""
        try:
            grouped_data = self._spark_df.groupBy(*cols)
            return LineageSparkGroupedData(grouped_data, self, list(cols))
        except Exception as e:
            logger.error(f"Error in groupBy operation: {str(e)}")
            return LineageSparkGroupedData(self._spark_df.groupBy(*cols), self, list(cols))

    def join(self, other: 'LineageSparkDataFrame', on=None, how: str = 'inner') -> 'LineageSparkDataFrame':
        """Join DataFrames with lineage tracking."""
        try:
            if isinstance(other, LineageSparkDataFrame):
                result_df = self._spark_df.join(
                    other._spark_df, on=on, how=how)
                other_spark_df = other
            else:
                result_df = self._spark_df.join(other, on=on, how=how)
                other_spark_df = LineageSparkDataFrame(other)

            target_table_name = f"{self.table_name}_join_{other_spark_df.table_name}"
            target_df = LineageSparkDataFrame(
                result_df,
                table_name=target_table_name,
                parent_nodes=[self.table_node.id, other_spark_df.table_node.id]
            )

            # Track both parents
            self._track_operation("join", target_df)
            other_spark_df._track_operation("join", target_df)

            return target_df

        except Exception as e:
            logger.error(f"Error in join operation: {str(e)}")
            if isinstance(other, LineageSparkDataFrame):
                return LineageSparkDataFrame(self._spark_df.join(other._spark_df, on=on, how=how))
            else:
                return LineageSparkDataFrame(self._spark_df.join(other, on=on, how=how))

    def withColumn(self, colName: str, col) -> 'LineageSparkDataFrame':
        """Add or replace column with lineage tracking."""
        try:
            result_df = self._spark_df.withColumn(colName, col)

            target_table_name = f"{self.table_name}_withColumn"
            target_df = LineageSparkDataFrame(
                result_df,
                table_name=target_table_name,
                parent_nodes=[self.table_node.id]
            )

            # All existing columns pass through, new column depends on source columns
            column_mappings = {existing_col: [existing_col]
                               for existing_col in self.column_nodes.keys()}

            # Try to extract dependencies for new column
            try:
                # Simple heuristic: if column expression contains existing column names
                col_str = str(col)
                source_cols = [existing_col for existing_col in self.column_nodes.keys()
                               if existing_col in col_str]
                if source_cols:
                    column_mappings[colName] = source_cols
            except:
                pass

            self._track_operation("withColumn", target_df, column_mappings)

            return target_df

        except Exception as e:
            logger.error(f"Error in withColumn operation: {str(e)}")
            return LineageSparkDataFrame(self._spark_df.withColumn(colName, col))

    def union(self, other: 'LineageSparkDataFrame') -> 'LineageSparkDataFrame':
        """Union DataFrames with lineage tracking."""
        try:
            if isinstance(other, LineageSparkDataFrame):
                result_df = self._spark_df.union(other._spark_df)
                other_spark_df = other
            else:
                result_df = self._spark_df.union(other)
                other_spark_df = LineageSparkDataFrame(other)

            target_table_name = f"{self.table_name}_union_{other_spark_df.table_name}"
            target_df = LineageSparkDataFrame(
                result_df,
                table_name=target_table_name,
                parent_nodes=[self.table_node.id, other_spark_df.table_node.id]
            )

            self._track_operation("union", target_df)
            other_spark_df._track_operation("union", target_df)

            return target_df

        except Exception as e:
            logger.error(f"Error in union operation: {str(e)}")
            if isinstance(other, LineageSparkDataFrame):
                return LineageSparkDataFrame(self._spark_df.union(other._spark_df))
            else:
                return LineageSparkDataFrame(self._spark_df.union(other))

    def cache(self) -> 'LineageSparkDataFrame':
        """Cache DataFrame with lineage tracking."""
        self._spark_df.cache()
        self.table_node.metadata['is_cached'] = True
        return self

    def persist(self, storageLevel=None) -> 'LineageSparkDataFrame':
        """Persist DataFrame with lineage tracking."""
        if storageLevel:
            self._spark_df.persist(storageLevel)
            self.table_node.metadata['storage_level'] = str(storageLevel)
        else:
            self._spark_df.persist()
        return self

    # Delegate other methods to underlying Spark DataFrame
    def __getattr__(self, name):
        """Delegate unknown methods to underlying Spark DataFrame."""
        attr = getattr(self._spark_df, name)

        if callable(attr):
            @wraps(attr)
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                # If result is a DataFrame, wrap it
                if hasattr(result, 'schema') and hasattr(result, 'rdd'):
                    return LineageSparkDataFrame(result)
                return result
            return wrapper
        return attr

    @property
    def spark_df(self) -> 'SparkDataFrame':
        """Get the underlying Spark DataFrame."""
        return self._spark_df


class LineageSparkGroupedData:
    """Wrapper around Spark GroupedData with lineage tracking."""

    def __init__(self, grouped_data, parent_df: LineageSparkDataFrame, group_cols: List[str]):
        """
        Initialize LineageSparkGroupedData.

        Args:
            grouped_data: Spark GroupedData object
            parent_df: Parent LineageSparkDataFrame
            group_cols: Grouping columns
        """
        self._grouped_data = grouped_data
        self.parent_df = parent_df
        self.group_cols = group_cols

    def agg(self, *exprs) -> LineageSparkDataFrame:
        """Aggregate with lineage tracking."""
        try:
            result_df = self._grouped_data.agg(*exprs)

            target_table_name = f"{self.parent_df.table_name}_agg"
            target_df = LineageSparkDataFrame(
                result_df,
                table_name=target_table_name,
                parent_nodes=[self.parent_df.table_node.id]
            )

            # Group columns pass through, aggregated columns depend on source
            column_mappings = {col: [col] for col in self.group_cols
                               if col in self.parent_df.column_nodes}

            self.parent_df._track_operation(
                "groupBy.agg", target_df, column_mappings)

            return target_df

        except Exception as e:
            logger.error(f"Error in agg operation: {str(e)}")
            return LineageSparkDataFrame(self._grouped_data.agg(*exprs))

    def count(self) -> LineageSparkDataFrame:
        """Count with lineage tracking."""
        return self.agg({'*': 'count'})

    def sum(self, *cols) -> LineageSparkDataFrame:
        """Sum with lineage tracking."""
        if cols:
            agg_dict = {col: 'sum' for col in cols}
            return self.agg(agg_dict)
        return self.agg({'*': 'sum'})

    def avg(self, *cols) -> LineageSparkDataFrame:
        """Average with lineage tracking."""
        if cols:
            agg_dict = {col: 'avg' for col in cols}
            return self.agg(agg_dict)
        return self.agg({'*': 'avg'})

    def __getattr__(self, name):
        """Delegate to underlying GroupedData."""
        attr = getattr(self._grouped_data, name)

        if callable(attr):
            @wraps(attr)
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                # If result is a DataFrame, wrap it
                if hasattr(result, 'schema') and hasattr(result, 'rdd'):
                    return LineageSparkDataFrame(result)
                return result
            return wrapper
        return attr

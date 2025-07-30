"""
DataFrame wrapper with lineage tracking capabilities.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Set, Union, Callable
import inspect

from .tracker import LineageTracker
from .nodes import TableNode, ColumnNode
from .edges import LineageEdge, TransformationType
from .config import get_config
from .operations import OperationTracker
from ..utils.dependency_analyzer import smart_column_dependency_detection


class LineageDataFrame:
    """
    A wrapper around pandas DataFrame that tracks data lineage.

    This class intercepts DataFrame operations and records lineage metadata
    while maintaining compatibility with pandas DataFrame API.
    """

    @staticmethod
    def concat(dataframes, **kwargs) -> 'LineageDataFrame':
        """
        Concatenate multiple LineageDataFrames.

        Args:
            dataframes: List of LineageDataFrames to concatenate
            **kwargs: Additional arguments passed to pandas.concat

        Returns:
            New LineageDataFrame with concatenated data
        """
        if not dataframes:
            raise ValueError("Cannot concatenate empty list of DataFrames")

        # Ensure all are LineageDataFrames
        for df in dataframes:
            if not isinstance(df, LineageDataFrame):
                raise TypeError("All DataFrames must be LineageDataFrames")

        # Perform concatenation
        pandas_dfs = [df._df for df in dataframes]
        result_df = pd.concat(pandas_dfs, **kwargs)

        # Create new LineageDataFrame
        first_df = dataframes[0]
        new_ldf = first_df._create_result_dataframe(result_df, "concat")

        # Track concatenation
        config = get_config()
        if config.enabled:
            # Get code context from the first DataFrame
            code_context, file_name, line_number = first_df._get_code_context()

            source_node_ids = [df._lineage_node_id for df in dataframes]
            all_input_columns = set()
            for df in dataframes:
                all_input_columns.update(df._df.columns)

            edge = LineageEdge(
                source_node_ids=source_node_ids,
                target_node_id=new_ldf._lineage_node_id,
                transformation_type=TransformationType.CONCAT,
                operation_name="concat",
                parameters=kwargs,
                code_context=code_context,
                file_name=file_name,
                line_number=line_number,
                input_columns=all_input_columns,
                output_columns=set(result_df.columns)
            )

            # Column mappings for concatenation
            for col in result_df.columns:
                source_cols = set()
                for df in dataframes:
                    if col in df._df.columns:
                        source_cols.add(col)
                if source_cols:
                    edge.add_column_mapping(col, source_cols)

            first_df._tracker.add_edge(edge)

        return new_ldf

    @staticmethod
    def from_pandas(df: pd.DataFrame, name: Optional[str] = None, **kwargs) -> 'LineageDataFrame':
        """
        Create a LineageDataFrame from an existing pandas DataFrame.

        Args:
            df: Pandas DataFrame to wrap
            name: Name for lineage tracking
            **kwargs: Additional arguments for LineageDataFrame

        Returns:
            New LineageDataFrame
        """
        return LineageDataFrame(df, name=name, **kwargs)

    def __init__(self, data=None, name: Optional[str] = None, source_type: str = "unknown",
                 source_location: Optional[str] = None, **kwargs):
        """
        Initialize a LineageDataFrame.

        Args:
            data: Data to create DataFrame from (same as pandas.DataFrame)
            name: Name for this DataFrame in lineage tracking
            source_type: Type of data source (csv, sql, parquet, etc.)
            source_location: Location/path of the data source
            **kwargs: Additional arguments passed to pandas.DataFrame
        """
        # Create the underlying pandas DataFrame
        if isinstance(data, pd.DataFrame):
            self._df = data.copy()
        else:
            self._df = pd.DataFrame(data, **kwargs)

        # Initialize lineage tracking
        self._tracker = LineageTracker.get_global_instance()
        self._lineage_node_id = None
        self._initialize_lineage_tracking(name, source_type, source_location)

    def _initialize_lineage_tracking(self, name: Optional[str], source_type: str,
                                     source_location: Optional[str]) -> None:
        """Initialize lineage tracking for this DataFrame."""
        config = get_config()
        if not config.enabled:
            return

        # Create table node
        table_node = TableNode(
            name=name or f"dataframe_{id(self)}",
            columns=set(self._df.columns),
            shape=self._df.shape,
            source_type=source_type,
            source_location=source_location
        )

        self._lineage_node_id = self._tracker.add_node(table_node)

        # Create column nodes if column-level tracking is enabled
        if config.tracking_level.value in ['column', 'full']:
            for col_name in self._df.columns:
                if config.is_column_tracked(col_name):
                    col_node = ColumnNode(
                        name=col_name,
                        table_id=self._lineage_node_id,
                        data_type=str(self._df[col_name].dtype),
                        nullable=self._df[col_name].isnull().any()
                    )
                    self._tracker.add_node(col_node)

    def _create_result_dataframe(self, result_df: pd.DataFrame,
                                 operation_name: str = "unknown") -> 'LineageDataFrame':
        """Create a new LineageDataFrame from a result DataFrame."""
        # Create new LineageDataFrame
        new_ldf = LineageDataFrame.__new__(LineageDataFrame)
        new_ldf._df = result_df
        new_ldf._tracker = self._tracker

        # Initialize lineage tracking for the result
        config = get_config()
        if config.enabled:
            table_node = TableNode(
                name=f"{operation_name}_result_{id(new_ldf)}",
                columns=set(result_df.columns),
                shape=result_df.shape,
                source_type="transformation"
            )
            new_ldf._lineage_node_id = self._tracker.add_node(table_node)

            # Create column nodes
            if config.tracking_level.value in ['column', 'full']:
                for col_name in result_df.columns:
                    if config.is_column_tracked(col_name):
                        col_node = ColumnNode(
                            name=col_name,
                            table_id=new_ldf._lineage_node_id,
                            data_type=str(result_df[col_name].dtype),
                            nullable=result_df[col_name].isnull().any()
                        )
                        self._tracker.add_node(col_node)
        else:
            new_ldf._lineage_node_id = None

        return new_ldf

    # Delegate attribute access to the underlying DataFrame
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying pandas DataFrame."""
        attr = getattr(self._df, name)

        # If it's a method that returns a DataFrame, wrap it
        if callable(attr) and name in self._TRACKED_METHODS:
            return self._wrap_method(attr, name)

        return attr

    def __getitem__(self, key) -> Union['LineageDataFrame', pd.Series]:
        """Handle DataFrame indexing with lineage tracking."""
        result = self._df[key]

        if isinstance(result, pd.DataFrame):
            # Column selection - track as SELECT operation
            if isinstance(key, (list, pd.Index)):
                selected_columns = list(key)
            elif isinstance(key, str):
                selected_columns = [key]
                result = pd.DataFrame(result)  # Convert Series to DataFrame
            else:
                # Complex indexing - treat as filter
                new_ldf = self._create_result_dataframe(result, "filter")
                OperationTracker.track_filter(self, new_ldf, str(key))
                return new_ldf

            new_ldf = self._create_result_dataframe(result, "select")
            OperationTracker.track_selection(self, new_ldf, selected_columns)
            return new_ldf

        return result  # Return Series as-is

    def __setitem__(self, key: str, value) -> None:
        """Handle DataFrame assignment with lineage tracking."""
        # Determine source columns for the assignment
        source_columns = set()

        if isinstance(value, pd.Series):
            # If assigning a Series, it might depend on other columns
            source_columns = set(self._df.columns)  # Conservative assumption
        elif callable(value):
            # If it's a function, we can't easily determine dependencies
            source_columns = set(self._df.columns)
        elif hasattr(value, '__iter__') and not isinstance(value, str):
            # If it's an iterable, assume it doesn't depend on existing columns
            source_columns = set()
        else:
            # Scalar value - no dependencies
            source_columns = set()

        # Perform the assignment
        self._df[key] = value

        # Track the assignment
        new_columns = {key: source_columns}
        OperationTracker.track_assignment(self, self, new_columns)

        # Core DataFrame methods with lineage tracking
    def assign(self, **kwargs) -> 'LineageDataFrame':
        """Assign new columns with lineage tracking."""
        result_df = self._df.assign(**kwargs)
        new_ldf = self._create_result_dataframe(result_df, "assign")

        # Determine column dependencies using smart analysis
        new_columns = {}
        for col_name, value in kwargs.items():
            if callable(value):
                # Use smart dependency detection
                referenced_cols = smart_column_dependency_detection(
                    value, list(self._df.columns))
                new_columns[col_name] = referenced_cols
            else:
                new_columns[col_name] = set()  # Scalar assignment

        OperationTracker.track_assignment(self, new_ldf, new_columns)
        return new_ldf

    def merge(self, right: 'LineageDataFrame', **kwargs) -> 'LineageDataFrame':
        """Merge with another LineageDataFrame with lineage tracking."""
        if not isinstance(right, LineageDataFrame):
            raise TypeError("Can only merge with another LineageDataFrame")

        result_df = self._df.merge(right._df, **kwargs)
        new_ldf = self._create_result_dataframe(result_df, "merge")

        # Track merge operation
        config = get_config()
        if config.enabled:
            code_context, file_name, line_number = self._get_code_context()

            edge = LineageEdge(
                source_node_ids=[self._lineage_node_id,
                                 right._lineage_node_id],
                target_node_id=new_ldf._lineage_node_id,
                transformation_type=TransformationType.MERGE,
                operation_name="merge",
                parameters=kwargs,
                code_context=code_context,
                file_name=file_name,
                line_number=line_number,
                input_columns=set(self._df.columns) | set(right._df.columns),
                output_columns=set(result_df.columns)
            )

            # Column mappings for merge
            for col in result_df.columns:
                source_cols = set()
                if col in self._df.columns:
                    source_cols.add(col)
                if col in right._df.columns:
                    source_cols.add(col)
                if source_cols:
                    edge.add_column_mapping(col, source_cols)

            self._tracker.add_edge(edge)

        return new_ldf

    def groupby(self, by=None, **kwargs):
        """GroupBy with lineage tracking."""
        # Return a custom GroupBy object that tracks operations
        return LineageGroupBy(self, by, **kwargs)

    def concat_with(self, others, **kwargs) -> 'LineageDataFrame':
        """Concatenate with other LineageDataFrames."""
        if not isinstance(others, list):
            others = [others]

        # Ensure all are LineageDataFrames
        for other in others:
            if not isinstance(other, LineageDataFrame):
                raise TypeError(
                    "Can only concatenate with other LineageDataFrames")

        # Perform concatenation
        all_dfs = [self._df] + [other._df for other in others]
        result_df = pd.concat(all_dfs, **kwargs)
        new_ldf = self._create_result_dataframe(result_df, "concat")

        # Track concatenation
        config = get_config()
        if config.enabled:
            code_context, file_name, line_number = self._get_code_context()

            source_node_ids = [self._lineage_node_id] + \
                [other._lineage_node_id for other in others]
            all_input_columns = set(self._df.columns)
            for other in others:
                all_input_columns.update(other._df.columns)

            edge = LineageEdge(
                source_node_ids=source_node_ids,
                target_node_id=new_ldf._lineage_node_id,
                transformation_type=TransformationType.CONCAT,
                operation_name="concat",
                parameters=kwargs,
                code_context=code_context,
                file_name=file_name,
                line_number=line_number,
                input_columns=all_input_columns,
                output_columns=set(result_df.columns)
            )

            # Column mappings for concatenation
            for col in result_df.columns:
                source_cols = set()
                if col in self._df.columns:
                    source_cols.add(col)
                for other in others:
                    if col in other._df.columns:
                        source_cols.add(col)
                if source_cols:
                    edge.add_column_mapping(col, source_cols)

            self._tracker.add_edge(edge)

        return new_ldf

    def drop(self, labels=None, axis=0, **kwargs) -> 'LineageDataFrame':
        """Drop columns or rows with lineage tracking."""
        result_df = self._df.drop(labels, axis=axis, **kwargs)
        new_ldf = self._create_result_dataframe(result_df, "drop")

        # Track drop operation
        config = get_config()
        if config.enabled:
            code_context, file_name, line_number = self._get_code_context()

            if axis == 1 or axis == 'columns':
                # Dropping columns
                dropped_cols = labels if isinstance(labels, list) else [labels]
                remaining_cols = [
                    col for col in self._df.columns if col not in dropped_cols]
            else:
                # Dropping rows - all columns remain
                remaining_cols = list(self._df.columns)

            edge = LineageEdge(
                source_node_ids=[self._lineage_node_id],
                target_node_id=new_ldf._lineage_node_id,
                transformation_type=TransformationType.SELECT,  # Drop is essentially a select
                operation_name="drop",
                parameters={'labels': labels, 'axis': axis, **kwargs},
                code_context=code_context,
                file_name=file_name,
                line_number=line_number,
                input_columns=set(self._df.columns),
                output_columns=set(remaining_cols)
            )

            # Column mappings for remaining columns
            for col in remaining_cols:
                edge.add_column_mapping(col, {col})

            self._tracker.add_edge(edge)

        return new_ldf

    def rename(self, mapper=None, **kwargs) -> 'LineageDataFrame':
        """Rename columns with lineage tracking."""
        # If mapper is provided and no axis/columns specified, assume columns
        if mapper is not None and 'columns' not in kwargs and 'index' not in kwargs:
            kwargs['columns'] = mapper
            result_df = self._df.rename(**kwargs)
        else:
            result_df = self._df.rename(mapper, **kwargs)
        new_ldf = self._create_result_dataframe(result_df, "rename")

        # Track rename operation
        config = get_config()
        if config.enabled:
            code_context, file_name, line_number = self._get_code_context()

            # Determine column mappings
            if isinstance(mapper, dict):
                column_mapping = mapper
            elif callable(mapper):
                # If mapper is a function, apply it to column names
                column_mapping = {col: mapper(col) for col in self._df.columns}
            else:
                column_mapping = {}

            edge = LineageEdge(
                source_node_ids=[self._lineage_node_id],
                target_node_id=new_ldf._lineage_node_id,
                transformation_type=TransformationType.SELECT,
                operation_name="rename",
                parameters={'mapper': str(mapper), **kwargs},
                code_context=code_context,
                file_name=file_name,
                line_number=line_number,
                input_columns=set(self._df.columns),
                output_columns=set(result_df.columns)
            )

            # Column mappings for rename
            for old_col, new_col in column_mapping.items():
                if old_col in self._df.columns:
                    edge.add_column_mapping(new_col, {old_col})

            # Handle columns that weren't renamed
            for col in self._df.columns:
                if col not in column_mapping and col in result_df.columns:
                    edge.add_column_mapping(col, {col})

            self._tracker.add_edge(edge)

        return new_ldf

    def apply(self, func, axis=0, **kwargs):
        """Apply function with lineage tracking."""
        result = self._df.apply(func, axis=axis, **kwargs)

        if isinstance(result, pd.DataFrame):
            new_ldf = self._create_result_dataframe(result, "apply")

            # Track apply operation
            config = get_config()
            if config.enabled:
                code_context, file_name, line_number = self._get_code_context()

                # Determine input/output columns based on axis and function analysis
                if axis == 0 or axis == 'index':
                    # Applied to each column - use smart dependency detection
                    input_cols = smart_column_dependency_detection(
                        func, list(self._df.columns))
                    output_cols = set(result.columns) if hasattr(
                        result, 'columns') else set()
                else:
                    # Applied to each row - typically uses all columns
                    input_cols = set(self._df.columns)
                    output_cols = set(result.columns) if hasattr(
                        result, 'columns') else set()

                edge = LineageEdge(
                    source_node_ids=[self._lineage_node_id],
                    target_node_id=new_ldf._lineage_node_id,
                    transformation_type=TransformationType.APPLY,
                    operation_name="apply",
                    parameters={'func': str(func), 'axis': axis, **kwargs},
                    code_context=code_context,
                    file_name=file_name,
                    line_number=line_number,
                    input_columns=input_cols,
                    output_columns=output_cols
                )

                # Conservative column mapping - assume all input columns affect all output columns
                for out_col in output_cols:
                    edge.add_column_mapping(out_col, input_cols)

                self._tracker.add_edge(edge)

            return new_ldf
        else:
            # Return Series or scalar as-is
            return result

    def pivot_table(self, values=None, index=None, columns=None, aggfunc='mean', **kwargs) -> 'LineageDataFrame':
        """Pivot table with lineage tracking."""
        result_df = self._df.pivot_table(values=values, index=index, columns=columns,
                                         aggfunc=aggfunc, **kwargs)
        new_ldf = self._create_result_dataframe(result_df, "pivot_table")

        # Track pivot operation
        config = get_config()
        if config.enabled:
            code_context, file_name, line_number = self._get_code_context()

            # Determine input columns
            input_cols = set()
            if values:
                if isinstance(values, list):
                    input_cols.update(values)
                else:
                    input_cols.add(values)
            if index:
                if isinstance(index, list):
                    input_cols.update(index)
                else:
                    input_cols.add(index)
            if columns:
                if isinstance(columns, list):
                    input_cols.update(columns)
                else:
                    input_cols.add(columns)

            edge = LineageEdge(
                source_node_ids=[self._lineage_node_id],
                target_node_id=new_ldf._lineage_node_id,
                transformation_type=TransformationType.PIVOT,
                operation_name="pivot_table",
                parameters={
                    'values': values, 'index': index, 'columns': columns,
                    'aggfunc': str(aggfunc), **kwargs
                },
                code_context=code_context,
                file_name=file_name,
                line_number=line_number,
                input_columns=input_cols,
                output_columns=set(result_df.columns)
            )

            # Column mappings for pivot - all output columns depend on input columns
            for out_col in result_df.columns:
                edge.add_column_mapping(str(out_col), input_cols)

            self._tracker.add_edge(edge)

        return new_ldf

    def melt(self, id_vars=None, value_vars=None, var_name=None, value_name='value', **kwargs) -> 'LineageDataFrame':
        """Melt (unpivot) with lineage tracking."""
        result_df = self._df.melt(id_vars=id_vars, value_vars=value_vars,
                                  var_name=var_name, value_name=value_name, **kwargs)
        new_ldf = self._create_result_dataframe(result_df, "melt")

        # Track melt operation
        config = get_config()
        if config.enabled:
            code_context, file_name, line_number = self._get_code_context()

            # Determine input columns
            input_cols = set()
            if id_vars:
                if isinstance(id_vars, list):
                    input_cols.update(id_vars)
                else:
                    input_cols.add(id_vars)
            if value_vars:
                if isinstance(value_vars, list):
                    input_cols.update(value_vars)
                else:
                    input_cols.add(value_vars)
            else:
                # If value_vars not specified, all non-id columns are used
                all_cols = set(self._df.columns)
                id_set = set(id_vars) if id_vars else set()
                input_cols.update(all_cols - id_set)

            edge = LineageEdge(
                source_node_ids=[self._lineage_node_id],
                target_node_id=new_ldf._lineage_node_id,
                transformation_type=TransformationType.MELT,
                operation_name="melt",
                parameters={
                    'id_vars': id_vars, 'value_vars': value_vars,
                    'var_name': var_name, 'value_name': value_name, **kwargs
                },
                code_context=code_context,
                file_name=file_name,
                line_number=line_number,
                input_columns=input_cols,
                output_columns=set(result_df.columns)
            )

            # Column mappings for melt
            if id_vars:
                id_list = id_vars if isinstance(id_vars, list) else [id_vars]
                for id_col in id_list:
                    if id_col in result_df.columns:
                        edge.add_column_mapping(id_col, {id_col})

            # Variable and value columns depend on the melted columns
            var_col = var_name if var_name else 'variable'
            if var_col in result_df.columns:
                edge.add_column_mapping(var_col, input_cols)
            if value_name in result_df.columns:
                edge.add_column_mapping(value_name, input_cols)

            self._tracker.add_edge(edge)

        return new_ldf

    # Utility methods for lineage
    def get_lineage_for_column(self, column_name: str) -> Dict[str, Any]:
        """Get lineage information for a specific column."""
        return self._tracker.get_column_lineage(column_name, self._lineage_node_id)

    def get_table_lineage(self) -> Dict[str, Any]:
        """Get lineage information for this table."""
        if self._lineage_node_id:
            return self._tracker.get_table_lineage(self._lineage_node_id)
        return {}

    def show_lineage_graph(self, **kwargs) -> None:
        """Display the lineage graph (will be implemented in Phase 4)."""
        print("Lineage visualization will be implemented in Phase 4")
        print(f"Current table lineage: {self.get_table_lineage()}")

    def export_lineage_dot(self, filename: str) -> None:
        """Export lineage to DOT format (will be implemented in Phase 4)."""
        print(
            f"DOT export will be implemented in Phase 4. Would export to: {filename}")

    def _get_code_context(self) -> tuple:
        """Get code context information."""
        code_context = None
        file_name = None
        line_number = None

        try:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_frame = frame.f_back
                file_name = caller_frame.f_code.co_filename
                line_number = caller_frame.f_lineno

                try:
                    source_lines = inspect.getframeinfo(
                        caller_frame).code_context
                    if source_lines:
                        code_context = ''.join(source_lines).strip()
                except:
                    pass
        except:
            pass
        finally:
            if 'frame' in locals():
                del frame

        return code_context, file_name, line_number

    def _wrap_method(self, method: Callable, method_name: str) -> Callable:
        """Wrap a DataFrame method to add lineage tracking."""
        def wrapper(*args, **kwargs):
            result = method(*args, **kwargs)

            if isinstance(result, pd.DataFrame):
                new_ldf = self._create_result_dataframe(result, method_name)
                # Add basic tracking for the method
                # More specific tracking will be added for each method type
                return new_ldf

            return result

        return wrapper

    # Methods that should be tracked
    _TRACKED_METHODS = {
        'drop', 'dropna', 'fillna', 'replace', 'rename',
        'sort_values', 'sort_index', 'reset_index', 'set_index',
        'pivot', 'pivot_table', 'melt', 'stack', 'unstack',
        'join', 'apply', 'applymap', 'transform'
    }

    # Delegate common DataFrame properties
    @property
    def columns(self):
        return self._df.columns

    @property
    def index(self):
        return self._df.index

    @property
    def shape(self):
        return self._df.shape

    @property
    def dtypes(self):
        return self._df.dtypes

    def __len__(self):
        return len(self._df)

    def __str__(self):
        return str(self._df)

    def __repr__(self):
        return f"LineageDataFrame(shape={self.shape}, lineage_id={self._lineage_node_id})\n{repr(self._df)}"


class LineageGroupBy:
    """GroupBy object with lineage tracking."""

    def __init__(self, parent_df: LineageDataFrame, by, **kwargs):
        self.parent_df = parent_df
        self.by = by
        self.kwargs = kwargs
        self._groupby = parent_df._df.groupby(by, **kwargs)

    def agg(self, func) -> LineageDataFrame:
        """Aggregate with lineage tracking."""
        result_df = self._groupby.agg(func)
        new_ldf = self.parent_df._create_result_dataframe(
            result_df, "groupby_agg")

        # Track aggregation
        config = get_config()
        if config.enabled:
            code_context, file_name, line_number = self.parent_df._get_code_context()

            groupby_cols = [self.by] if isinstance(
                self.by, str) else list(self.by)

            edge = LineageEdge(
                source_node_ids=[self.parent_df._lineage_node_id],
                target_node_id=new_ldf._lineage_node_id,
                transformation_type=TransformationType.AGGREGATE,
                operation_name="groupby_agg",
                parameters={'by': groupby_cols, 'func': str(func)},
                code_context=code_context,
                file_name=file_name,
                line_number=line_number,
                input_columns=set(self.parent_df._df.columns),
                output_columns=set(result_df.columns)
            )

            # Column mappings for aggregation
            for col in result_df.columns:
                if col in groupby_cols:
                    edge.add_column_mapping(col, {col})
                else:
                    # Aggregated columns depend on the original column
                    edge.add_column_mapping(col, {col})

            self.parent_df._tracker.add_edge(edge)

        return new_ldf

    def mean(self) -> LineageDataFrame:
        """Mean aggregation with lineage tracking."""
        return self.agg('mean')

    def sum(self) -> LineageDataFrame:
        """Sum aggregation with lineage tracking."""
        return self.agg('sum')

    def count(self) -> LineageDataFrame:
        """Count aggregation with lineage tracking."""
        return self.agg('count')

    def min(self) -> LineageDataFrame:
        """Min aggregation with lineage tracking."""
        return self.agg('min')

    def max(self) -> LineageDataFrame:
        """Max aggregation with lineage tracking."""
        return self.agg('max')

    def std(self) -> LineageDataFrame:
        """Standard deviation aggregation with lineage tracking."""
        return self.agg('std')

    def var(self) -> LineageDataFrame:
        """Variance aggregation with lineage tracking."""
        return self.agg('var')

    def median(self) -> LineageDataFrame:
        """Median aggregation with lineage tracking."""
        return self.agg('median')

    def first(self) -> LineageDataFrame:
        """First value aggregation with lineage tracking."""
        return self.agg('first')

    def last(self) -> LineageDataFrame:
        """Last value aggregation with lineage tracking."""
        return self.agg('last')

    def size(self) -> LineageDataFrame:
        """Size aggregation with lineage tracking."""
        result_df = self._groupby.size().reset_index(name='size')
        new_ldf = self.parent_df._create_result_dataframe(
            result_df, "groupby_size")

        # Track size operation
        config = get_config()
        if config.enabled:
            code_context, file_name, line_number = self.parent_df._get_code_context()

            groupby_cols = [self.by] if isinstance(
                self.by, str) else list(self.by)

            edge = LineageEdge(
                source_node_ids=[self.parent_df._lineage_node_id],
                target_node_id=new_ldf._lineage_node_id,
                transformation_type=TransformationType.AGGREGATE,
                operation_name="groupby_size",
                parameters={'by': groupby_cols},
                code_context=code_context,
                file_name=file_name,
                line_number=line_number,
                input_columns=set(self.parent_df._df.columns),
                output_columns=set(result_df.columns)
            )

            # Column mappings for size
            for col in groupby_cols:
                if col in result_df.columns:
                    edge.add_column_mapping(col, {col})
            edge.add_column_mapping('size', set(self.parent_df._df.columns))

            self.parent_df._tracker.add_edge(edge)

        return new_ldf

    def nunique(self) -> LineageDataFrame:
        """Number of unique values aggregation with lineage tracking."""
        return self.agg('nunique')

    def __getattr__(self, name):
        """Delegate to the underlying GroupBy object."""
        attr = getattr(self._groupby, name)
        if callable(attr) and name in ['mean', 'sum', 'count', 'min', 'max', 'std', 'var', 'median', 'first', 'last', 'nunique']:
            def wrapper(*args, **kwargs):
                result_df = attr(*args, **kwargs)
                if hasattr(result_df, 'reset_index'):
                    result_df = result_df.reset_index()
                return self.parent_df._create_result_dataframe(result_df, f"groupby_{name}")
            return wrapper
        return attr

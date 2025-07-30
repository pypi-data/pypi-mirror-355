"""
LineageDataFrame - A wrapper around pandas DataFrame that automatically tracks lineage.
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Union
import functools

from .tracker import default_tracker
from .nodes import DataNode
from .operations import PandasOperation


class LineageDataFrame:
    """
    A wrapper around pandas DataFrame that automatically tracks data lineage.

    This class intercepts pandas operations and records them in the lineage graph,
    providing transparent lineage tracking without changing user code.
    """

    def __init__(self,
                 data: Union[pd.DataFrame, Dict, List],
                 name: Optional[str] = None,
                 tracker=None,
                 source_node: Optional[DataNode] = None):
        """
        Initialize a LineageDataFrame.

        Args:
            data: The underlying pandas DataFrame or data to create one
            name: Optional name for this DataFrame
            tracker: LineageTracker instance to use (defaults to global tracker)
            source_node: Optional source node if this DataFrame comes from a specific source
        """
        # Convert to pandas DataFrame if needed
        if isinstance(data, pd.DataFrame):
            self._df = data
        else:
            self._df = pd.DataFrame(data)

        self.name = name or f"dataframe_{id(self)}"
        self.tracker = tracker or default_tracker

        # Create or use provided source node
        if source_node:
            self.node = source_node
        else:
            self.node = self.tracker.create_node("data", self.name)

        # Update node schema
        self._update_node_schema()

    def _update_node_schema(self):
        """Update the lineage node with current DataFrame schema."""
        schema = {}
        for col in self._df.columns:
            dtype = str(self._df[col].dtype)
            schema[col] = dtype
        self.node.set_schema(schema)

    def _create_operation_wrapper(self, method_name: str):
        """Create a wrapper for pandas operations that tracks lineage."""
        original_method = getattr(self._df, method_name)

        @functools.wraps(original_method)
        def wrapper(*args, **kwargs):
            # Execute the original pandas operation
            result = original_method(*args, **kwargs)

            # If result is a DataFrame, wrap it and track the operation
            if isinstance(result, pd.DataFrame):
                # Create new LineageDataFrame for the result
                result_name = f"{self.name}_{method_name}"
                result_ldf = LineageDataFrame(
                    result,
                    name=result_name,
                    tracker=self.tracker
                )

                # Track the operation
                operation = PandasOperation(
                    operation_type=method_name,
                    inputs=[self.node.id],
                    outputs=[result_ldf.node.id],
                    method_name=method_name,
                    args=args,
                    kwargs=kwargs
                )

                self.tracker.operations.append(operation)
                self.tracker.add_edge(self.node, result_ldf.node, operation)

                return result_ldf
            else:
                # For non-DataFrame results, return as-is
                return result

        return wrapper

    def __getattr__(self, name):
        """Intercept attribute access to wrap pandas methods."""
        if hasattr(self._df, name):
            attr = getattr(self._df, name)

            # If it's a method that returns a DataFrame, wrap it
            if callable(attr) and name in self._trackable_methods():
                return self._create_operation_wrapper(name)
            else:
                return attr
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'")

    def _trackable_methods(self) -> List[str]:
        """Return list of pandas methods that should be tracked."""
        return [
            # Selection and filtering
            'query', 'loc', 'iloc', 'head', 'tail', 'sample',

            # Transformation
            'drop', 'drop_duplicates', 'dropna', 'fillna', 'replace',
            'rename', 'astype', 'assign', 'pipe', 'copy',

            # Grouping and aggregation
            'groupby', 'agg', 'aggregate', 'sum', 'mean', 'count',
            'min', 'max', 'std', 'var', 'median',

            # Merging and joining
            'merge', 'join', 'concat', 'append',

            # Reshaping
            'pivot', 'pivot_table', 'melt', 'stack', 'unstack',
            'transpose', 'T',

            # Sorting
            'sort_values', 'sort_index', 'nlargest', 'nsmallest',

            # String operations (for string columns)
            'str',

            # Mathematical operations
            'abs', 'round', 'clip', 'rank',

            # Window operations
            'rolling', 'expanding', 'ewm',
        ]

    # Delegate common DataFrame properties
    @property
    def shape(self):
        return self._df.shape

    @property
    def columns(self):
        return self._df.columns

    @property
    def index(self):
        return self._df.index

    @property
    def dtypes(self):
        return self._df.dtypes

    @property
    def values(self):
        return self._df.values

    def __len__(self):
        return len(self._df)

    def __getitem__(self, key):
        """Handle DataFrame indexing operations."""
        result = self._df[key]

        if isinstance(result, pd.DataFrame):
            # Create new LineageDataFrame for subset
            result_name = f"{self.name}_subset"
            result_ldf = LineageDataFrame(
                result,
                name=result_name,
                tracker=self.tracker
            )

            # Track the selection operation
            operation = PandasOperation(
                operation_type="selection",
                inputs=[self.node.id],
                outputs=[result_ldf.node.id],
                method_name="__getitem__",
                args=(key,),
                kwargs={}
            )

            self.tracker.operations.append(operation)
            self.tracker.add_edge(self.node, result_ldf.node, operation)

            return result_ldf
        else:
            # Return Series as-is (could be extended to track Series lineage)
            return result

    def __setitem__(self, key, value):
        """Handle DataFrame assignment operations."""
        self._df[key] = value
        self._update_node_schema()

    def __add__(self, other):
        """Handle addition operations."""
        if isinstance(other, LineageDataFrame):
            result = self._df + other._df
            result_name = f"{self.name}_add_{other.name}"
            result_ldf = LineageDataFrame(
                result, name=result_name, tracker=self.tracker)

            # Track the operation
            operation = PandasOperation(
                operation_type="add",
                inputs=[self.node.id, other.node.id],
                outputs=[result_ldf.node.id],
                method_name="__add__",
                args=(other,),
                kwargs={}
            )

            self.tracker.operations.append(operation)
            self.tracker.add_edge(self.node, result_ldf.node, operation)
            self.tracker.add_edge(other.node, result_ldf.node, operation)

            return result_ldf
        else:
            result = self._df + other
            result_name = f"{self.name}_add_scalar"
            result_ldf = LineageDataFrame(
                result, name=result_name, tracker=self.tracker)

            # Track the operation
            operation = PandasOperation(
                operation_type="add_scalar",
                inputs=[self.node.id],
                outputs=[result_ldf.node.id],
                method_name="__add__",
                args=(other,),
                kwargs={}
            )

            self.tracker.operations.append(operation)
            self.tracker.add_edge(self.node, result_ldf.node, operation)

            return result_ldf

    def to_pandas(self) -> pd.DataFrame:
        """Return the underlying pandas DataFrame."""
        return self._df

    def get_lineage(self, direction: str = 'both') -> Dict:
        """Get lineage information for this DataFrame."""
        return self.tracker.get_lineage(self.node.id, direction)

    def __str__(self):
        return f"LineageDataFrame(name='{self.name}', shape={self.shape})\n{str(self._df)}"

    def __repr__(self):
        return f"LineageDataFrame(name='{self.name}', shape={self.shape})"

    # Delegate display methods
    def head(self, n=5):
        """Return first n rows as LineageDataFrame."""
        result = self._df.head(n)
        result_name = f"{self.name}_head_{n}"
        result_ldf = LineageDataFrame(
            result,
            name=result_name,
            tracker=self.tracker
        )

        # Track the operation
        operation = PandasOperation(
            operation_type="head",
            inputs=[self.node.id],
            outputs=[result_ldf.node.id],
            method_name="head",
            args=(n,),
            kwargs={}
        )

        self.tracker.operations.append(operation)
        self.tracker.add_edge(self.node, result_ldf.node, operation)

        return result_ldf

    def info(self, *args, **kwargs):
        """Delegate to pandas info method."""
        return self._df.info(*args, **kwargs)

    def describe(self, *args, **kwargs):
        """Delegate to pandas describe method."""
        return self._df.describe(*args, **kwargs)


def read_csv(filepath: str,
             name: Optional[str] = None,
             tracker=None,
             **kwargs) -> LineageDataFrame:
    """
    Read CSV file and return LineageDataFrame with automatic lineage tracking.

    Args:
        filepath: Path to CSV file
        name: Optional name for the DataFrame
        tracker: LineageTracker instance to use
        **kwargs: Additional arguments passed to pandas.read_csv

    Returns:
        LineageDataFrame instance
    """
    # Read the CSV file
    df = pd.read_csv(filepath, **kwargs)

    # Create file node
    tracker = tracker or default_tracker
    file_node = tracker.create_node("file", filepath, {
        'file_format': 'csv',
        'file_path': filepath
    })

    # Create LineageDataFrame
    name = name or f"csv_{filepath}"
    ldf = LineageDataFrame(df, name=name, tracker=tracker)

    # Track the read operation
    operation = PandasOperation(
        operation_type="read_csv",
        inputs=[file_node.id],
        outputs=[ldf.node.id],
        method_name="read_csv",
        args=(filepath,),
        kwargs=kwargs
    )

    tracker.operations.append(operation)
    tracker.add_edge(file_node, ldf.node, operation)

    return ldf

"""
Operation tracking and custom function registration for lineage.
"""

import inspect
import functools
from typing import Dict, List, Set, Any, Optional, Callable, Union
from dataclasses import dataclass

from .tracker import LineageTracker
from .edges import LineageEdge, TransformationType
from .config import get_config


@dataclass
class OperationMetadata:
    """Metadata for tracking operations."""

    input_columns: Set[str]
    output_columns: Set[str]
    transformation_type: TransformationType
    operation_name: str
    parameters: Dict[str, Any]
    description: Optional[str] = None


# Global registry for custom operations
_custom_operations: Dict[str, OperationMetadata] = {}


def register_lineage_transform(
    input_cols: Union[List[str], Set[str]],
    output_cols: Union[List[str], Set[str]],
    transformation_type: TransformationType = TransformationType.CUSTOM,
    operation_name: Optional[str] = None,
    description: Optional[str] = None
) -> Callable:
    """
    Decorator to register custom functions for lineage tracking.
    """
    def decorator(func: Callable) -> Callable:
        nonlocal operation_name
        if operation_name is None:
            operation_name = func.__name__

        # Store operation metadata
        metadata = OperationMetadata(
            input_columns=set(input_cols),
            output_columns=set(output_cols),
            transformation_type=transformation_type,
            operation_name=operation_name,
            parameters={},
            description=description
        )
        _custom_operations[operation_name] = metadata

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Track lineage if enabled
            config = get_config()
            if config.enabled:
                _track_custom_operation(func, args, kwargs, result, metadata)

            return result

        wrapper._lineage_metadata = metadata
        return wrapper

    return decorator


def _track_custom_operation(func, args, kwargs, result, metadata):
    """Track a custom operation in the lineage graph."""
    try:
        tracker = LineageTracker.get_global_instance()

        # Try to extract DataFrame arguments
        dataframes = []
        for arg in args:
            if hasattr(arg, '_lineage_node_id'):  # LineageDataFrame
                dataframes.append(arg)

        for value in kwargs.values():
            if hasattr(value, '_lineage_node_id'):  # LineageDataFrame
                dataframes.append(value)

        if not dataframes:
            return  # No trackable DataFrames found

        # Get code context
        code_context, file_name, line_number = _get_code_context()

        # Create lineage edge
        edge = LineageEdge(
            source_node_ids=[df._lineage_node_id for df in dataframes],
            target_node_id=getattr(result, '_lineage_node_id', ''),
            transformation_type=metadata.transformation_type,
            operation_name=metadata.operation_name,
            parameters=metadata.parameters.copy(),
            code_context=code_context,
            file_name=file_name,
            line_number=line_number,
            function_name=func.__name__,
            input_columns=metadata.input_columns.copy(),
            output_columns=metadata.output_columns.copy()
        )

        # Add column mappings
        for output_col in metadata.output_columns:
            edge.add_column_mapping(output_col, metadata.input_columns)

        tracker.add_edge(edge)

    except Exception as e:
        # Don't let lineage tracking break the actual computation
        config = get_config()
        if config.enable_performance_monitoring:
            print(
                f"Warning: Failed to track lineage for {metadata.operation_name}: {e}")


def get_operation_metadata(operation_name: str) -> Optional[OperationMetadata]:
    """Get metadata for a registered operation."""
    return _custom_operations.get(operation_name)


def list_registered_operations() -> List[str]:
    """List all registered custom operations."""
    return list(_custom_operations.keys())


def clear_registered_operations() -> None:
    """Clear all registered operations (useful for testing)."""
    _custom_operations.clear()


class OperationTracker:
    """Helper class for tracking DataFrame operations."""

    @staticmethod
    def track_selection(
        source_df: Any,
        result_df: Any,
        selected_columns: List[str],
        operation_name: str = "select"
    ) -> None:
        """Track column selection operation."""
        config = get_config()
        if not config.enabled:
            return

        tracker = LineageTracker.get_global_instance()

        # Get code context
        code_context, file_name, line_number = _get_code_context()

        edge = LineageEdge(
            source_node_ids=[getattr(source_df, '_lineage_node_id', '')],
            target_node_id=getattr(result_df, '_lineage_node_id', ''),
            transformation_type=TransformationType.SELECT,
            operation_name=operation_name,
            parameters={'selected_columns': selected_columns},
            code_context=code_context,
            file_name=file_name,
            line_number=line_number,
            input_columns=set(selected_columns),
            output_columns=set(selected_columns)
        )

        # Direct column mapping for selection
        for col in selected_columns:
            edge.add_column_mapping(col, {col})

        tracker.add_edge(edge)

    @staticmethod
    def track_filter(
        source_df: Any,
        result_df: Any,
        filter_condition: str,
        operation_name: str = "filter"
    ) -> None:
        """Track filtering operation."""
        config = get_config()
        if not config.enabled:
            return

        tracker = LineageTracker.get_global_instance()

        # Get code context
        code_context, file_name, line_number = _get_code_context()

        # For filters, all columns pass through unchanged
        source_columns = set(getattr(source_df, 'columns', []))

        edge = LineageEdge(
            source_node_ids=[getattr(source_df, '_lineage_node_id', '')],
            target_node_id=getattr(result_df, '_lineage_node_id', ''),
            transformation_type=TransformationType.FILTER,
            operation_name=operation_name,
            parameters={'filter_condition': filter_condition},
            code_context=code_context,
            file_name=file_name,
            line_number=line_number,
            input_columns=source_columns,
            output_columns=source_columns
        )

        # All columns map to themselves in a filter
        for col in source_columns:
            edge.add_column_mapping(col, {col})

        tracker.add_edge(edge)

    @staticmethod
    def track_assignment(
        source_df: Any,
        result_df: Any,
        new_columns: Dict[str, Set[str]],  # new_col -> {source_cols}
        operation_name: str = "assign"
    ) -> None:
        """Track column assignment/creation operation."""
        config = get_config()
        if not config.enabled:
            return

        tracker = LineageTracker.get_global_instance()

        # Get code context
        code_context, file_name, line_number = _get_code_context()

        all_input_cols = set()
        all_output_cols = set(new_columns.keys())

        for source_cols in new_columns.values():
            all_input_cols.update(source_cols)

        edge = LineageEdge(
            source_node_ids=[getattr(source_df, '_lineage_node_id', '')],
            target_node_id=getattr(result_df, '_lineage_node_id', ''),
            transformation_type=TransformationType.ASSIGN,
            operation_name=operation_name,
            parameters={'new_columns': {
                k: list(v) for k, v in new_columns.items()}},
            code_context=code_context,
            file_name=file_name,
            line_number=line_number,
            input_columns=all_input_cols,
            output_columns=all_output_cols
        )

        # Add column mappings
        for new_col, source_cols in new_columns.items():
            edge.add_column_mapping(new_col, source_cols)

        tracker.add_edge(edge)


def _get_code_context() -> tuple:
    """Get code context information from the call stack."""
    code_context = None
    file_name = None
    line_number = None

    try:
        frame = inspect.currentframe()
        if frame and frame.f_back and frame.f_back.f_back:
            caller_frame = frame.f_back.f_back
            file_name = caller_frame.f_code.co_filename
            line_number = caller_frame.f_lineno

            # Try to get source code context
            try:
                source_lines = inspect.getframeinfo(caller_frame).code_context
                if source_lines:
                    code_context = ''.join(source_lines).strip()
            except:
                pass
    except:
        pass
    finally:
        if 'frame' in locals():
            del frame  # Prevent reference cycles

    return code_context, file_name, line_number

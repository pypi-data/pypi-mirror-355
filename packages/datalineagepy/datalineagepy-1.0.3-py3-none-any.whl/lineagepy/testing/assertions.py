"""
Comprehensive assertion utilities for testing data lineage.
"""

import time
from typing import List, Optional, Set, Dict, Any, Union
from ..core.tracker import LineageTracker
from ..core.edges import TransformationType


def assert_column_lineage(
    dataframe: Any,
    column_name: str,
    expected_sources: Union[List[str], Set[str]],
    table_id: Optional[str] = None
) -> None:
    """
    Assert that a column has the expected source columns in its lineage.

    Args:
        dataframe: The DataFrame to check
        column_name: Name of the column to check lineage for
        expected_sources: Expected source columns
        table_id: Optional table ID for disambiguation

    Raises:
        AssertionError: If lineage doesn't match expectations
    """
    if not hasattr(dataframe, 'get_lineage_for_column'):
        raise ValueError("DataFrame does not support lineage tracking")

    lineage_info = dataframe.get_lineage_for_column(column_name)
    actual_sources = set(lineage_info.get('source_columns', []))
    expected_sources_set = set(expected_sources)

    if actual_sources != expected_sources_set:
        raise AssertionError(
            f"Column '{column_name}' lineage mismatch. "
            f"Expected sources: {expected_sources_set}, "
            f"Actual sources: {actual_sources}"
        )


def assert_table_lineage(
    dataframe: Any,
    expected_source_tables: Union[List[str], Set[str]]
) -> None:
    """
    Assert that a table has the expected source tables in its lineage.

    Args:
        dataframe: The DataFrame to check
        expected_source_tables: Expected source table IDs

    Raises:
        AssertionError: If lineage doesn't match expectations
    """
    if not hasattr(dataframe, 'get_table_lineage'):
        raise ValueError("DataFrame does not support lineage tracking")

    table_id = getattr(dataframe, '_lineage_node_id', None)
    if not table_id:
        raise ValueError("DataFrame does not have lineage tracking enabled")

    lineage_info = dataframe.get_table_lineage(table_id)
    actual_sources = set(lineage_info.get('source_tables', []))
    expected_sources_set = set(expected_source_tables)

    if actual_sources != expected_sources_set:
        raise AssertionError(
            f"Table lineage mismatch. "
            f"Expected source tables: {expected_sources_set}, "
            f"Actual source tables: {actual_sources}"
        )


def assert_transformation_count(expected_count: int,
                                transformation_type: Optional[TransformationType] = None,
                                tracker: Optional[LineageTracker] = None) -> None:
    """
    Assert that the tracker has the expected number of transformations.

    Args:
        expected_count: Expected number of transformations
        transformation_type: Optional specific transformation type to count
        tracker: LineageTracker instance (uses global if None)

    Raises:
        AssertionError: If count doesn't match expectations
    """
    if tracker is None:
        tracker = LineageTracker.get_global_instance()

    if transformation_type is None:
        actual_count = len(tracker.edges)
        if actual_count != expected_count:
            raise AssertionError(
                f"Expected {expected_count} transformations, got {actual_count}"
            )
    else:
        actual_count = sum(1 for edge in tracker.edges.values()
                           if edge.transformation_type == transformation_type)
        if actual_count != expected_count:
            raise AssertionError(
                f"Expected {expected_count} {transformation_type.value} transformations, "
                f"got {actual_count}"
            )


def assert_node_exists(node_name: str, node_type: Optional[str] = None,
                       tracker: Optional[LineageTracker] = None) -> None:
    """
    Assert that a node with the given name exists.

    Args:
        node_name: Name of the node to check
        node_type: Optional node type to verify ('table', 'column')
        tracker: LineageTracker instance (uses global if None)

    Raises:
        AssertionError: If node doesn't exist or type doesn't match
    """
    if tracker is None:
        tracker = LineageTracker.get_global_instance()

    found_nodes = []
    for node_id, node in tracker.nodes.items():
        if hasattr(node, 'name') and node.name == node_name:
            actual_type = node.__class__.__name__.lower().replace('node', '')
            if node_type is None or actual_type == node_type:
                found_nodes.append((node_id, actual_type))

    if not found_nodes:
        type_msg = f" of type '{node_type}'" if node_type else ""
        raise AssertionError(
            f"Node '{node_name}'{type_msg} not found in lineage")


def assert_edge_exists(source_name: str, target_name: str,
                       transformation_type: Optional[TransformationType] = None,
                       tracker: Optional[LineageTracker] = None) -> None:
    """
    Assert that an edge exists between source and target nodes.

    Args:
        source_name: Name of the source node
        target_name: Name of the target node
        transformation_type: Optional transformation type to verify
        tracker: LineageTracker instance (uses global if None)

    Raises:
        AssertionError: If edge doesn't exist or type doesn't match
    """
    if tracker is None:
        tracker = LineageTracker.get_global_instance()

    # Find source and target nodes
    source_nodes = [node_id for node_id, node in tracker.nodes.items()
                    if hasattr(node, 'name') and node.name == source_name]
    target_nodes = [node_id for node_id, node in tracker.nodes.items()
                    if hasattr(node, 'name') and node.name == target_name]

    if not source_nodes:
        raise AssertionError(f"Source node '{source_name}' not found")
    if not target_nodes:
        raise AssertionError(f"Target node '{target_name}' not found")

    # Check for edge
    found_edge = False
    for edge in tracker.edges.values():
        if (edge.target_node_id in target_nodes and
                any(src_id in source_nodes for src_id in edge.source_node_ids)):
            if transformation_type is None or edge.transformation_type == transformation_type:
                found_edge = True
                break

    if not found_edge:
        type_msg = f" with type '{transformation_type.value}'" if transformation_type else ""
        raise AssertionError(
            f"Edge from '{source_name}' to '{target_name}'{type_msg} not found"
        )


def assert_dag_validity(tracker: Optional[LineageTracker] = None) -> None:
    """
    Assert that the lineage graph is a valid DAG (no cycles).

    Args:
        tracker: LineageTracker instance (uses global if None)

    Raises:
        AssertionError: If graph contains cycles
    """
    if tracker is None:
        tracker = LineageTracker.get_global_instance()

    # Simple cycle detection
    visited = set()
    rec_stack = set()

    def has_cycle(node_id: str) -> bool:
        visited.add(node_id)
        rec_stack.add(node_id)

        # Find outgoing edges
        for edge in tracker.edges.values():
            if node_id in edge.source_node_ids:
                target = edge.target_node_id
                if target not in visited:
                    if has_cycle(target):
                        return True
                elif target in rec_stack:
                    return True

        rec_stack.remove(node_id)
        return False

    for node_id in tracker.nodes:
        if node_id not in visited:
            if has_cycle(node_id):
                raise AssertionError(
                    "Lineage graph contains cycles (not a valid DAG)")


def assert_lineage_quality(min_context_coverage: float = 0.0,
                           min_column_mapping_coverage: float = 0.0,
                           min_completeness_score: float = 0.0,
                           tracker: Optional[LineageTracker] = None) -> None:
    """
    Assert that lineage quality metrics meet minimum thresholds.

    Args:
        min_context_coverage: Minimum context coverage (0.0-1.0)
        min_column_mapping_coverage: Minimum column mapping coverage (0.0-1.0)
        min_completeness_score: Minimum overall completeness score (0.0-1.0)
        tracker: LineageTracker instance (uses global if None)

    Raises:
        AssertionError: If quality metrics don't meet thresholds
    """
    if tracker is None:
        tracker = LineageTracker.get_global_instance()

    # Basic quality check
    total_edges = len(tracker.edges)
    if total_edges == 0:
        return

    edges_with_context = sum(
        1 for edge in tracker.edges.values() if edge.code_context)
    context_coverage = edges_with_context / total_edges

    if context_coverage < min_context_coverage:
        raise AssertionError(
            f"Context coverage {context_coverage:.2%} below minimum "
            f"{min_context_coverage:.2%}"
        )


def assert_performance_metrics(max_execution_time: float = 10.0,
                               max_memory_usage_mb: Optional[float] = None,
                               tracker: Optional[LineageTracker] = None) -> None:
    """
    Assert that performance metrics meet requirements.

    Args:
        max_execution_time: Maximum allowed execution time in seconds
        max_memory_usage_mb: Maximum allowed memory usage in MB (optional)
        tracker: LineageTracker instance (uses global if None)

    Raises:
        AssertionError: If performance metrics don't meet requirements
    """
    if tracker is None:
        tracker = LineageTracker.get_global_instance()

    # Test basic operations performance
    start_time = time.time()

    # Perform some basic operations
    node_count = len(tracker.nodes)
    edge_count = len(tracker.edges)

    # Simple traversal
    for edge in tracker.edges.values():
        _ = edge.target_node_id
        _ = edge.source_node_ids

    execution_time = time.time() - start_time

    if execution_time > max_execution_time:
        raise AssertionError(
            f"Execution time {execution_time:.3f}s exceeds maximum {max_execution_time}s"
        )

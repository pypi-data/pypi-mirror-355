"""
Comprehensive validation classes for data lineage testing.
"""

import time
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from ..core.tracker import LineageTracker
from ..core.edges import TransformationType


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class LineageValidator:
    """
    Comprehensive validator for lineage graph structure and integrity.
    """

    def __init__(self, tracker: Optional[LineageTracker] = None):
        """
        Initialize the validator.

        Args:
            tracker: LineageTracker instance. If None, uses global instance.
        """
        self.tracker = tracker or LineageTracker.get_global_instance()

    def validate_graph_integrity(self) -> ValidationResult:
        """
        Validate the overall integrity of the lineage graph.

        Returns:
            ValidationResult with overall integrity status
        """
        issues = []
        details = {}

        # Check for orphaned nodes (but exclude column nodes from original DataFrames)
        referenced_nodes = set()
        for edge in self.tracker.edges.values():
            referenced_nodes.add(edge.target_node_id)
            referenced_nodes.update(edge.source_node_ids)

        orphaned_nodes = set(self.tracker.nodes.keys()) - referenced_nodes

        # Filter out column nodes from original DataFrames (these are expected to be "orphaned")
        problematic_orphaned_nodes = []
        for node_id in orphaned_nodes:
            node = self.tracker.nodes.get(node_id)
            if node:
                node_type = node.__class__.__name__.lower().replace('node', '')
                # Only consider table nodes as problematic if orphaned
                # Column nodes can be orphaned if they're not used in transformations
                if node_type == 'table':
                    problematic_orphaned_nodes.append(node_id)

        if problematic_orphaned_nodes:
            issues.append(
                f"Found {len(problematic_orphaned_nodes)} problematic orphaned table nodes")
            details['problematic_orphaned_nodes'] = problematic_orphaned_nodes

        # Report all orphaned nodes for information, but don't fail on column nodes
        if orphaned_nodes:
            details['all_orphaned_nodes'] = list(orphaned_nodes)
            details['orphaned_column_nodes'] = len(
                orphaned_nodes) - len(problematic_orphaned_nodes)

        # Check for dangling references
        dangling_refs = []
        for edge_id, edge in self.tracker.edges.items():
            if edge.target_node_id not in self.tracker.nodes:
                dangling_refs.append(
                    f"Edge {edge_id} references missing target {edge.target_node_id}")

            for source_id in edge.source_node_ids:
                if source_id not in self.tracker.nodes:
                    dangling_refs.append(
                        f"Edge {edge_id} references missing source {source_id}")

        if dangling_refs:
            issues.append(f"Found {len(dangling_refs)} dangling references")
            details['dangling_references'] = dangling_refs

        # Check for duplicate edges
        edge_signatures = {}
        duplicate_edges = []
        for edge_id, edge in self.tracker.edges.items():
            signature = (tuple(sorted(edge.source_node_ids)),
                         edge.target_node_id, edge.transformation_type)
            if signature in edge_signatures:
                duplicate_edges.append((edge_id, edge_signatures[signature]))
            else:
                edge_signatures[signature] = edge_id

        if duplicate_edges:
            issues.append(f"Found {len(duplicate_edges)} duplicate edges")
            details['duplicate_edges'] = duplicate_edges

        passed = len(issues) == 0
        message = "Graph integrity validation passed" if passed else f"Graph integrity issues: {'; '.join(issues)}"

        return ValidationResult(passed=passed, message=message, details=details)

    def validate_dag_structure(self) -> ValidationResult:
        """
        Validate that the graph is a valid DAG (no cycles).

        Returns:
            ValidationResult with DAG validation status
        """
        try:
            # Use topological sort to detect cycles
            visited = set()
            rec_stack = set()
            cycle_path = []

            def has_cycle(node_id: str, path: List[str]) -> bool:
                visited.add(node_id)
                rec_stack.add(node_id)
                path.append(node_id)

                # Find outgoing edges
                for edge in self.tracker.edges.values():
                    if node_id in edge.source_node_ids:
                        target = edge.target_node_id
                        if target not in visited:
                            if has_cycle(target, path):
                                return True
                        elif target in rec_stack:
                            # Found cycle
                            cycle_start = path.index(target)
                            cycle_path.extend(path[cycle_start:] + [target])
                            return True

                rec_stack.remove(node_id)
                path.pop()
                return False

            for node_id in self.tracker.nodes:
                if node_id not in visited:
                    if has_cycle(node_id, []):
                        return ValidationResult(
                            passed=False,
                            message=f"Graph contains cycle: {' -> '.join(cycle_path)}",
                            details={'cycle_path': cycle_path}
                        )

            return ValidationResult(
                passed=True,
                message="Graph is a valid DAG (no cycles detected)",
                details={'node_count': len(
                    self.tracker.nodes), 'edge_count': len(self.tracker.edges)}
            )

        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"DAG validation failed with error: {str(e)}",
                details={'error': str(e)}
            )

    def validate_node_consistency(self) -> ValidationResult:
        """
        Validate consistency of node data and relationships.

        Returns:
            ValidationResult with node consistency status
        """
        issues = []
        details = {}

        # Check node data consistency
        node_types = {}
        for node_id, node in self.tracker.nodes.items():
            node_type = node.__class__.__name__
            node_types[node_type] = node_types.get(node_type, 0) + 1

            # Check required attributes
            if not hasattr(node, 'name') or not node.name:
                issues.append(f"Node {node_id} missing or empty name")

            if not hasattr(node, 'created_at'):
                issues.append(f"Node {node_id} missing created_at timestamp")

        details['node_type_distribution'] = node_types

        # Check for naming conflicts
        name_conflicts = {}
        for node_id, node in self.tracker.nodes.items():
            if hasattr(node, 'name'):
                name = node.name
                node_type = node.__class__.__name__
                key = (name, node_type)
                if key not in name_conflicts:
                    name_conflicts[key] = []
                name_conflicts[key].append(node_id)

        conflicts = {k: v for k, v in name_conflicts.items() if len(v) > 1}
        if conflicts:
            issues.append(f"Found {len(conflicts)} naming conflicts")
            details['naming_conflicts'] = conflicts

        passed = len(issues) == 0
        message = "Node consistency validation passed" if passed else f"Node consistency issues: {'; '.join(issues)}"

        return ValidationResult(passed=passed, message=message, details=details)


class QualityValidator:
    """
    Validator for lineage quality metrics and completeness.
    """

    def __init__(self, tracker: Optional[LineageTracker] = None):
        """
        Initialize the quality validator.

        Args:
            tracker: LineageTracker instance. If None, uses global instance.
        """
        self.tracker = tracker or LineageTracker.get_global_instance()

    def validate_context_coverage(self, min_coverage: float = 0.8) -> ValidationResult:
        """
        Validate that edges have sufficient context information.

        Args:
            min_coverage: Minimum required context coverage (0.0-1.0)

        Returns:
            ValidationResult with context coverage status
        """
        total_edges = len(self.tracker.edges)
        if total_edges == 0:
            return ValidationResult(
                passed=True,
                message="No edges to validate context coverage",
                details={'total_edges': 0, 'coverage': 1.0}
            )

        edges_with_context = sum(
            1 for edge in self.tracker.edges.values() if edge.code_context)
        coverage = edges_with_context / total_edges

        passed = coverage >= min_coverage
        message = (f"Context coverage {coverage:.2%} {'meets' if passed else 'below'} "
                   f"minimum {min_coverage:.2%}")

        return ValidationResult(
            passed=passed,
            message=message,
            details={
                'total_edges': total_edges,
                'edges_with_context': edges_with_context,
                'coverage': coverage,
                'min_required': min_coverage
            }
        )

    def validate_column_mapping_coverage(self, min_coverage: float = 0.7) -> ValidationResult:
        """
        Validate that edges have sufficient column mapping information.

        Args:
            min_coverage: Minimum required column mapping coverage (0.0-1.0)

        Returns:
            ValidationResult with column mapping coverage status
        """
        total_edges = len(self.tracker.edges)
        if total_edges == 0:
            return ValidationResult(
                passed=True,
                message="No edges to validate column mapping coverage",
                details={'total_edges': 0, 'coverage': 1.0}
            )

        edges_with_mapping = sum(
            1 for edge in self.tracker.edges.values() if edge.column_mapping)
        coverage = edges_with_mapping / total_edges

        passed = coverage >= min_coverage
        message = (f"Column mapping coverage {coverage:.2%} {'meets' if passed else 'below'} "
                   f"minimum {min_coverage:.2%}")

        return ValidationResult(
            passed=passed,
            message=message,
            details={
                'total_edges': total_edges,
                'edges_with_mapping': edges_with_mapping,
                'coverage': coverage,
                'min_required': min_coverage
            }
        )

    def validate_transformation_diversity(self, min_types: int = 3) -> ValidationResult:
        """
        Validate that the lineage includes diverse transformation types.

        Args:
            min_types: Minimum number of different transformation types

        Returns:
            ValidationResult with transformation diversity status
        """
        transformation_types = set()
        for edge in self.tracker.edges.values():
            transformation_types.add(edge.transformation_type)

        type_count = len(transformation_types)
        passed = type_count >= min_types

        message = (f"Found {type_count} transformation types, "
                   f"{'meets' if passed else 'below'} minimum {min_types}")

        return ValidationResult(
            passed=passed,
            message=message,
            details={
                'transformation_types': [t.value for t in transformation_types],
                'type_count': type_count,
                'min_required': min_types
            }
        )


class PerformanceValidator:
    """
    Validator for performance characteristics and scalability.
    """

    def __init__(self, tracker: Optional[LineageTracker] = None):
        """
        Initialize the performance validator.

        Args:
            tracker: LineageTracker instance. If None, uses global instance.
        """
        self.tracker = tracker or LineageTracker.get_global_instance()

    def validate_operation_performance(self, max_time: float = 1.0) -> ValidationResult:
        """
        Validate that basic operations complete within time limits.

        Args:
            max_time: Maximum allowed time for operations in seconds

        Returns:
            ValidationResult with performance status
        """
        operations = []

        # Test node access
        start_time = time.time()
        node_count = len(self.tracker.nodes)
        operations.append(('node_access', time.time() - start_time))

        # Test edge access
        start_time = time.time()
        edge_count = len(self.tracker.edges)
        operations.append(('edge_access', time.time() - start_time))

        # Test iteration
        start_time = time.time()
        for _ in self.tracker.nodes.values():
            pass
        operations.append(('node_iteration', time.time() - start_time))

        start_time = time.time()
        for _ in self.tracker.edges.values():
            pass
        operations.append(('edge_iteration', time.time() - start_time))

        # Check if any operation exceeded time limit
        slow_operations = [(op, t) for op, t in operations if t > max_time]

        passed = len(slow_operations) == 0
        total_time = sum(t for _, t in operations)

        message = (f"Performance validation {'passed' if passed else 'failed'}: "
                   f"total time {total_time:.3f}s")

        if slow_operations:
            message += f", slow operations: {slow_operations}"

        return ValidationResult(
            passed=passed,
            message=message,
            details={
                'operations': dict(operations),
                'total_time': total_time,
                'slow_operations': slow_operations,
                'node_count': node_count,
                'edge_count': edge_count
            }
        )

    def validate_memory_efficiency(self, max_mb_per_node: float = 1.0) -> ValidationResult:
        """
        Validate memory efficiency of the lineage tracking.

        Args:
            max_mb_per_node: Maximum MB per node allowed

        Returns:
            ValidationResult with memory efficiency status
        """
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            node_count = len(self.tracker.nodes)

            if node_count == 0:
                return ValidationResult(
                    passed=True,
                    message="No nodes to validate memory efficiency",
                    details={'memory_mb': memory_mb, 'node_count': 0}
                )

            mb_per_node = memory_mb / node_count
            passed = mb_per_node <= max_mb_per_node

            message = (f"Memory efficiency: {mb_per_node:.2f} MB/node "
                       f"({'within' if passed else 'exceeds'} limit of {max_mb_per_node:.2f} MB/node)")

            return ValidationResult(
                passed=passed,
                message=message,
                details={
                    'total_memory_mb': memory_mb,
                    'node_count': node_count,
                    'mb_per_node': mb_per_node,
                    'max_allowed': max_mb_per_node
                }
            )

        except ImportError:
            return ValidationResult(
                passed=True,
                message="Memory validation skipped (psutil not available)",
                details={'skipped': True}
            )


class SchemaValidator:
    """
    Validator for schema consistency and data type tracking.
    """

    def __init__(self, tracker: Optional[LineageTracker] = None):
        """
        Initialize the schema validator.

        Args:
            tracker: LineageTracker instance. If None, uses global instance.
        """
        self.tracker = tracker or LineageTracker.get_global_instance()

    def validate_column_schema_consistency(self) -> ValidationResult:
        """
        Validate that column schemas are consistent across transformations.

        Returns:
            ValidationResult with schema consistency status
        """
        issues = []
        details = {}

        # Group columns by name
        columns_by_name = {}
        for node_id, node in self.tracker.nodes.items():
            node_type = node.__class__.__name__.lower().replace('node', '')
            if node_type == 'column' and hasattr(node, 'name'):
                name = node.name
                if name not in columns_by_name:
                    columns_by_name[name] = []
                columns_by_name[name].append((node_id, node))

        # Check for schema inconsistencies
        schema_issues = {}
        for column_name, column_instances in columns_by_name.items():
            if len(column_instances) > 1:
                # Check data types
                data_types = set()
                for node_id, node in column_instances:
                    if hasattr(node, 'data_type') and node.data_type:
                        data_types.add(node.data_type)

                if len(data_types) > 1:
                    schema_issues[column_name] = {
                        'issue': 'inconsistent_data_types',
                        'data_types': list(data_types),
                        'instances': len(column_instances)
                    }

        if schema_issues:
            issues.append(
                f"Found {len(schema_issues)} columns with schema inconsistencies")
            details['schema_issues'] = schema_issues

        details['columns_analyzed'] = len(columns_by_name)
        details['total_column_instances'] = sum(
            len(instances) for instances in columns_by_name.values())

        passed = len(issues) == 0
        message = ("Schema consistency validation passed" if passed else
                   f"Schema consistency issues: {'; '.join(issues)}")

        return ValidationResult(passed=passed, message=message, details=details)

    def validate_table_schema_evolution(self) -> ValidationResult:
        """
        Validate that table schema evolution is properly tracked.

        Returns:
            ValidationResult with schema evolution status
        """
        issues = []
        details = {}

        # Group tables by name
        tables_by_name = {}
        for node_id, node in self.tracker.nodes.items():
            node_type = node.__class__.__name__.lower().replace('node', '')
            if node_type == 'table' and hasattr(node, 'name'):
                name = node.name
                if name not in tables_by_name:
                    tables_by_name[name] = []
                tables_by_name[name].append((node_id, node))

        # Check for schema evolution tracking
        evolution_tracking = {}
        for table_name, table_instances in tables_by_name.items():
            if len(table_instances) > 1:
                # Sort by creation time
                sorted_instances = sorted(table_instances,
                                          key=lambda x: getattr(x[1], 'created_at', 0))

                # Check column evolution
                column_sets = []
                for node_id, node in sorted_instances:
                    if hasattr(node, 'columns'):
                        column_sets.append(set(node.columns))
                    else:
                        column_sets.append(set())

                evolution_tracking[table_name] = {
                    'instances': len(table_instances),
                    'column_evolution': column_sets
                }

        details['tables_with_evolution'] = len(evolution_tracking)
        details['evolution_tracking'] = evolution_tracking

        passed = True  # Schema evolution is informational, not a failure
        message = f"Schema evolution analysis completed for {len(evolution_tracking)} tables"

        return ValidationResult(passed=passed, message=message, details=details)

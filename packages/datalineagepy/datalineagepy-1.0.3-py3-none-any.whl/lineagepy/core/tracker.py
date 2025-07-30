"""
Core lineage tracking functionality.
"""

import threading
from typing import Dict, List, Optional, Set, Any, Tuple
from collections import defaultdict, deque
import networkx as nx

from .nodes import LineageNode, TableNode, ColumnNode
from .edges import LineageEdge, TransformationType
from .config import get_config, LineageLevel


class LineageTracker:
    """Main class for tracking data lineage."""

    _global_instance: Optional['LineageTracker'] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialize the lineage tracker."""
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, LineageNode] = {}
        self.edges: Dict[str, LineageEdge] = {}
        self.table_nodes: Dict[str, TableNode] = {}
        self.column_nodes: Dict[str, ColumnNode] = {}

        # Performance optimization: maintain reverse lookup
        self.node_to_edges: Dict[str, Set[str]] = defaultdict(set)
        self.column_to_table: Dict[str, str] = {}

        # Cache for expensive operations
        self._lineage_cache: Dict[str, Any] = {}
        self._cache_enabled = True

    @classmethod
    def get_global_instance(cls) -> 'LineageTracker':
        """Get or create the global lineage tracker instance."""
        if cls._global_instance is None:
            with cls._lock:
                if cls._global_instance is None:
                    cls._global_instance = cls()
        return cls._global_instance

    @classmethod
    def reset_global_instance(cls) -> None:
        """Reset the global instance (useful for testing)."""
        with cls._lock:
            cls._global_instance = None

    def add_node(self, node: LineageNode) -> str:
        """Add a node to the lineage graph."""
        config = get_config()

        if not config.enabled:
            return node.id

        # Check node limits
        if len(self.nodes) >= config.max_nodes:
            raise RuntimeError(
                f"Maximum number of nodes ({config.max_nodes}) exceeded")

        self.nodes[node.id] = node
        self.graph.add_node(node.id, **node.to_dict())

        # Maintain type-specific lookups
        if isinstance(node, TableNode):
            self.table_nodes[node.id] = node
        elif isinstance(node, ColumnNode):
            self.column_nodes[node.id] = node
            if node.table_id:
                self.column_to_table[node.id] = node.table_id

        # Clear cache when graph changes
        self._clear_cache()

        return node.id

    def add_edge(self, edge: LineageEdge) -> str:
        """Add an edge to the lineage graph."""
        config = get_config()

        if not config.enabled:
            return edge.id

        # Check if operation should be tracked
        if not config.is_operation_tracked(edge.operation_name):
            return edge.id

        # Check edge limits
        if len(self.edges) >= config.max_edges:
            raise RuntimeError(
                f"Maximum number of edges ({config.max_edges}) exceeded")

        self.edges[edge.id] = edge

        # Add edges to graph
        for source_id in edge.source_node_ids:
            if source_id in self.nodes and edge.target_node_id in self.nodes:
                self.graph.add_edge(source_id, edge.target_node_id,
                                    edge_id=edge.id, **edge.to_dict())

                # Maintain reverse lookup
                self.node_to_edges[source_id].add(edge.id)
                self.node_to_edges[edge.target_node_id].add(edge.id)

        # Clear cache when graph changes
        self._clear_cache()

        return edge.id

    def get_node(self, node_id: str) -> Optional[LineageNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[LineageEdge]:
        """Get an edge by ID."""
        return self.edges.get(edge_id)

    def get_table_node(self, table_id: str) -> Optional[TableNode]:
        """Get a table node by ID."""
        return self.table_nodes.get(table_id)

    def get_column_lineage(self, column_name: str, table_id: Optional[str] = None) -> Dict[str, Any]:
        """Get lineage information for a specific column."""
        cache_key = f"column_lineage_{column_name}_{table_id}"

        if self._cache_enabled and cache_key in self._lineage_cache:
            return self._lineage_cache[cache_key]

        result = self._compute_column_lineage(column_name, table_id)

        if self._cache_enabled:
            self._lineage_cache[cache_key] = result

        return result

    def _compute_column_lineage(self, column_name: str, table_id: Optional[str] = None) -> Dict[str, Any]:
        """Compute column lineage (internal method)."""
        lineage_info = {
            'column': column_name,
            'table_id': table_id,
            'source_columns': set(),
            'transformation_path': [],
            'direct_dependencies': set(),
            'all_dependencies': set()
        }

        # Find the column node
        target_column_node = None
        for col_id, col_node in self.column_nodes.items():
            if col_node.name == column_name:
                if table_id is None or col_node.table_id == table_id:
                    target_column_node = col_node
                    break

        if not target_column_node:
            return lineage_info

        # Traverse backwards through the graph
        visited = set()
        queue = deque([(target_column_node.id, [])])

        while queue:
            current_node_id, path = queue.popleft()

            if current_node_id in visited:
                continue
            visited.add(current_node_id)

            # Get incoming edges
            for edge_id in self.node_to_edges.get(current_node_id, set()):
                edge = self.edges.get(edge_id)
                if not edge or current_node_id not in [edge.target_node_id]:
                    continue

                # Add transformation to path
                new_path = path + [edge.to_dict()]

                # Process source nodes
                for source_id in edge.source_node_ids:
                    source_node = self.nodes.get(source_id)
                    if source_node:
                        if isinstance(source_node, ColumnNode):
                            lineage_info['source_columns'].add(
                                source_node.name)
                            if len(path) == 0:  # Direct dependency
                                lineage_info['direct_dependencies'].add(
                                    source_node.name)
                            lineage_info['all_dependencies'].add(
                                source_node.name)

                        queue.append((source_id, new_path))

        lineage_info['transformation_path'] = list(
            lineage_info['transformation_path'])
        lineage_info['source_columns'] = list(lineage_info['source_columns'])
        lineage_info['direct_dependencies'] = list(
            lineage_info['direct_dependencies'])
        lineage_info['all_dependencies'] = list(
            lineage_info['all_dependencies'])

        return lineage_info

    def get_table_lineage(self, table_id: str) -> Dict[str, Any]:
        """Get lineage information for a table."""
        cache_key = f"table_lineage_{table_id}"

        if self._cache_enabled and cache_key in self._lineage_cache:
            return self._lineage_cache[cache_key]

        result = self._compute_table_lineage(table_id)

        if self._cache_enabled:
            self._lineage_cache[cache_key] = result

        return result

    def _compute_table_lineage(self, table_id: str) -> Dict[str, Any]:
        """Compute table lineage (internal method)."""
        lineage_info = {
            'table_id': table_id,
            'source_tables': set(),
            'transformation_path': [],
            'direct_dependencies': set(),
            'all_dependencies': set()
        }

        table_node = self.table_nodes.get(table_id)
        if not table_node:
            return lineage_info

        # Use NetworkX to find predecessors
        try:
            predecessors = list(nx.ancestors(self.graph, table_id))
            for pred_id in predecessors:
                pred_node = self.nodes.get(pred_id)
                if pred_node and isinstance(pred_node, TableNode):
                    lineage_info['source_tables'].add(pred_id)
                    lineage_info['all_dependencies'].add(pred_id)

            # Direct dependencies
            direct_preds = list(self.graph.predecessors(table_id))
            for pred_id in direct_preds:
                pred_node = self.nodes.get(pred_id)
                if pred_node and isinstance(pred_node, TableNode):
                    lineage_info['direct_dependencies'].add(pred_id)

        except nx.NetworkXError:
            pass  # Node not in graph

        lineage_info['source_tables'] = list(lineage_info['source_tables'])
        lineage_info['direct_dependencies'] = list(
            lineage_info['direct_dependencies'])
        lineage_info['all_dependencies'] = list(
            lineage_info['all_dependencies'])

        return lineage_info

    def get_downstream_impact(self, node_id: str) -> List[str]:
        """Get all nodes that would be impacted by changes to the given node."""
        try:
            return list(nx.descendants(self.graph, node_id))
        except nx.NetworkXError:
            return []

    def get_upstream_sources(self, node_id: str) -> List[str]:
        """Get all upstream source nodes for the given node."""
        try:
            return list(nx.ancestors(self.graph, node_id))
        except nx.NetworkXError:
            return []

    def export_graph(self, format: str = "dict") -> Any:
        """Export the lineage graph in various formats."""
        if format == "dict":
            return {
                'nodes': {node_id: node.to_dict() for node_id, node in self.nodes.items()},
                'edges': {edge_id: edge.to_dict() for edge_id, edge in self.edges.items()}
            }
        elif format == "networkx":
            return self.graph
        elif format == "json":
            import json
            return json.dumps(self.export_graph("dict"), indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def clear(self) -> None:
        """Clear all lineage data."""
        self.graph.clear()
        self.nodes.clear()
        self.edges.clear()
        self.table_nodes.clear()
        self.column_nodes.clear()
        self.node_to_edges.clear()
        self.column_to_table.clear()
        self._clear_cache()

    def _clear_cache(self) -> None:
        """Clear the internal cache."""
        self._lineage_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the lineage graph."""
        return {
            'total_nodes': len(self.nodes),
            'table_nodes': len(self.table_nodes),
            'column_nodes': len(self.column_nodes),
            'total_edges': len(self.edges),
            'graph_density': nx.density(self.graph) if self.nodes else 0,
            'cache_size': len(self._lineage_cache),
            'cache_enabled': self._cache_enabled
        }

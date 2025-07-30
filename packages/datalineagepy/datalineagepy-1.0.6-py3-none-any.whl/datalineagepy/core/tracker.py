"""
LineageTracker - Core class for tracking data lineage in pandas and PySpark workflows.
"""

import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import pandas as pd

from .nodes import DataNode, FileNode, DatabaseNode
from .edges import LineageEdge
from .operations import Operation


class LineageTracker:
    """
    Main class for tracking data lineage across pandas and PySpark operations.

    This tracker maintains a graph of data transformations, capturing:
    - Data sources (files, databases, APIs)
    - Transformations (operations, functions)
    - Data sinks (output files, databases)
    - Column-level lineage
    """

    def __init__(self, name: str = "default"):
        """
        Initialize a new LineageTracker.

        Args:
            name: Name identifier for this tracker instance
        """
        self.name = name
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        # Graph storage
        self.nodes: Dict[str, DataNode] = {}
        self.edges: List[LineageEdge] = []
        self.operations: List[Operation] = []

        # Tracking state
        self.active = True
        self._current_operation = None

    def create_node(self,
                    node_type: str,
                    name: str,
                    metadata: Optional[Dict] = None) -> DataNode:
        """
        Create a new data node in the lineage graph.

        Args:
            node_type: Type of node ('data', 'file', 'database')
            name: Unique name for the node
            metadata: Additional metadata about the node

        Returns:
            Created DataNode instance
        """
        if node_type == 'file':
            node = FileNode(name, metadata or {})
        elif node_type == 'database':
            node = DatabaseNode(name, metadata or {})
        else:
            node = DataNode(name, metadata or {})

        self.nodes[node.id] = node
        return node

    def add_edge(self,
                 source_node: DataNode,
                 target_node: DataNode,
                 operation: Optional[Operation] = None,
                 metadata: Optional[Dict] = None) -> LineageEdge:
        """
        Add a lineage edge between two nodes.

        Args:
            source_node: Source data node
            target_node: Target data node  
            operation: Operation that created this edge
            metadata: Additional edge metadata

        Returns:
            Created LineageEdge instance
        """
        edge = LineageEdge(
            source_id=source_node.id,
            target_id=target_node.id,
            operation=operation,
            metadata=metadata or {}
        )

        self.edges.append(edge)
        return edge

    def track_operation(self,
                        operation_type: str,
                        inputs: List[DataNode],
                        outputs: List[DataNode],
                        metadata: Optional[Dict] = None) -> Operation:
        """
        Track a data operation with its inputs and outputs.

        Args:
            operation_type: Type of operation (e.g., 'merge', 'filter', 'aggregate')
            inputs: List of input data nodes
            outputs: List of output data nodes
            metadata: Additional operation metadata

        Returns:
            Created Operation instance
        """
        operation = Operation(
            operation_type=operation_type,
            inputs=[node.id for node in inputs],
            outputs=[node.id for node in outputs],
            metadata=metadata or {}
        )

        self.operations.append(operation)

        # Create edges for this operation
        for input_node in inputs:
            for output_node in outputs:
                self.add_edge(input_node, output_node, operation)

        return operation

    def get_lineage(self, node_id: str, direction: str = 'both') -> Dict:
        """
        Get lineage information for a specific node.

        Args:
            node_id: ID of the node to trace
            direction: Direction to trace ('upstream', 'downstream', 'both')

        Returns:
            Dictionary containing lineage information
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in tracker")

        result = {
            'node': self.nodes[node_id].to_dict(),
            'upstream': [],
            'downstream': []
        }

        if direction in ['upstream', 'both']:
            result['upstream'] = self._get_upstream_nodes(node_id)

        if direction in ['downstream', 'both']:
            result['downstream'] = self._get_downstream_nodes(node_id)

        return result

    def _get_upstream_nodes(self, node_id: str) -> List[Dict]:
        """Get all upstream nodes for a given node."""
        upstream = []
        visited = set()

        def traverse_upstream(current_id):
            if current_id in visited:
                return
            visited.add(current_id)

            for edge in self.edges:
                if edge.target_id == current_id:
                    source_node = self.nodes[edge.source_id]
                    upstream.append({
                        'node': source_node.to_dict(),
                        'edge': edge.to_dict()
                    })
                    traverse_upstream(edge.source_id)

        traverse_upstream(node_id)
        return upstream

    def _get_downstream_nodes(self, node_id: str) -> List[Dict]:
        """Get all downstream nodes for a given node."""
        downstream = []
        visited = set()

        def traverse_downstream(current_id):
            if current_id in visited:
                return
            visited.add(current_id)

            for edge in self.edges:
                if edge.source_id == current_id:
                    target_node = self.nodes[edge.target_id]
                    downstream.append({
                        'node': target_node.to_dict(),
                        'edge': edge.to_dict()
                    })
                    traverse_downstream(edge.target_id)

        traverse_downstream(node_id)
        return downstream

    def get_stats(self) -> Dict:
        """
        Get statistics about the current lineage graph.

        Returns:
            Dictionary with graph statistics
        """
        return {
            'tracker_id': self.id,
            'tracker_name': self.name,
            'created_at': self.created_at.isoformat(),
            'nodes_count': len(self.nodes),
            'edges_count': len(self.edges),
            'operations_count': len(self.operations),
            'node_types': self._count_node_types(),
            'operation_types': self._count_operation_types()
        }

    def _count_node_types(self) -> Dict[str, int]:
        """Count nodes by type."""
        counts = {}
        for node in self.nodes.values():
            node_type = type(node).__name__
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts

    def _count_operation_types(self) -> Dict[str, int]:
        """Count operations by type."""
        counts = {}
        for operation in self.operations:
            op_type = operation.operation_type
            counts[op_type] = counts.get(op_type, 0) + 1
        return counts

    def export_graph(self, format: str = 'dict') -> Any:
        """
        Export the lineage graph in various formats.

        Args:
            format: Export format ('dict', 'json', 'graphml')

        Returns:
            Graph data in specified format
        """
        graph_data = {
            'metadata': self.get_stats(),
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges],
            'operations': [op.to_dict() for op in self.operations]
        }

        if format == 'dict':
            return graph_data
        elif format == 'json':
            import json
            return json.dumps(graph_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def clear(self):
        """Clear all tracked lineage data."""
        self.nodes.clear()
        self.edges.clear()
        self.operations.clear()

    def __str__(self) -> str:
        return f"LineageTracker(name='{self.name}', nodes={len(self.nodes)}, edges={len(self.edges)})"

    def __repr__(self) -> str:
        return self.__str__()


# Global default tracker instance
default_tracker = LineageTracker("global_default")

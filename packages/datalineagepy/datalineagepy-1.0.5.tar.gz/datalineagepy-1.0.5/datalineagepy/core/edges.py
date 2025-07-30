"""
LineageEdge class for representing connections between data nodes in the lineage graph.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime


class LineageEdge:
    """
    Represents a directed edge in the data lineage graph.

    An edge connects two data nodes and represents a data transformation,
    data movement, or dependency relationship.
    """

    def __init__(self,
                 source_id: str,
                 target_id: str,
                 operation: Optional['Operation'] = None,
                 metadata: Optional[Dict] = None):
        """
        Initialize a lineage edge.

        Args:
            source_id: ID of the source data node
            target_id: ID of the target data node
            operation: Operation that created this edge
            metadata: Additional metadata about the edge
        """
        self.id = str(uuid.uuid4())
        self.source_id = source_id
        self.target_id = target_id
        self.operation = operation
        self.created_at = datetime.now()
        self.metadata = metadata or {}

        # Column-level lineage
        self.column_mappings: Dict[str, List[str]] = {}

    def add_column_mapping(self, target_column: str, source_columns: List[str]):
        """
        Add column-level lineage mapping.

        Args:
            target_column: Name of the target column
            source_columns: List of source columns that contribute to the target
        """
        self.column_mappings[target_column] = source_columns

    def get_column_mapping(self, target_column: str) -> List[str]:
        """
        Get source columns for a target column.

        Args:
            target_column: Name of the target column

        Returns:
            List of source column names
        """
        return self.column_mappings.get(target_column, [])

    def get_all_column_mappings(self) -> Dict[str, List[str]]:
        """Get all column mappings for this edge."""
        return self.column_mappings.copy()

    def to_dict(self) -> Dict:
        """Convert edge to dictionary representation."""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'operation_id': self.operation.id if self.operation else None,
            'operation_type': self.operation.operation_type if self.operation else None,
            'created_at': self.created_at.isoformat(),
            'column_mappings': self.column_mappings,
            'metadata': self.metadata
        }

    def __str__(self) -> str:
        op_type = self.operation.operation_type if self.operation else "unknown"
        return f"LineageEdge(source={self.source_id[:8]}..., target={self.target_id[:8]}..., op={op_type})"

    def __repr__(self) -> str:
        return self.__str__()


class ColumnLineage:
    """
    Represents column-level lineage information.

    This class tracks how individual columns flow through transformations
    and can represent complex column relationships like splits, merges, and derivations.
    """

    def __init__(self, target_column: str):
        """
        Initialize column lineage tracking.

        Args:
            target_column: Name of the target column being tracked
        """
        self.target_column = target_column
        self.source_columns: List[str] = []
        self.transformation_type = "direct"  # direct, derived, split, merge
        self.transformation_logic = ""
        self.confidence_score = 1.0  # 0.0 to 1.0

    def add_source_column(self, column_name: str, confidence: float = 1.0):
        """Add a source column dependency."""
        if column_name not in self.source_columns:
            self.source_columns.append(column_name)
        # Update confidence (take minimum for conservative estimate)
        self.confidence_score = min(self.confidence_score, confidence)

    def set_transformation(self, transformation_type: str, logic: str = ""):
        """
        Set the transformation type and logic.

        Args:
            transformation_type: Type of transformation (direct, derived, split, merge)
            logic: Description of the transformation logic
        """
        self.transformation_type = transformation_type
        self.transformation_logic = logic

    def to_dict(self) -> Dict:
        """Convert column lineage to dictionary representation."""
        return {
            'target_column': self.target_column,
            'source_columns': self.source_columns,
            'transformation_type': self.transformation_type,
            'transformation_logic': self.transformation_logic,
            'confidence_score': self.confidence_score
        }

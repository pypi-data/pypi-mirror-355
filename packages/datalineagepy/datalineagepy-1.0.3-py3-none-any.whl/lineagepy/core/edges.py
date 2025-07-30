"""
Edge classes for representing transformations in the lineage graph.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum


class TransformationType(Enum):
    """Types of transformations that can be tracked."""

    SELECT = "select"
    FILTER = "filter"
    ASSIGN = "assign"
    MERGE = "merge"
    JOIN = "join"
    GROUPBY = "groupby"
    AGGREGATE = "aggregate"
    CONCAT = "concat"
    PIVOT = "pivot"
    MELT = "melt"
    APPLY = "apply"
    MAP = "map"
    CUSTOM = "custom"
    UNKNOWN = "unknown"

    # Spark-specific transformations
    SPARK_OPERATION = "spark_operation"
    SPARK_SQL = "spark_sql"
    SPARK_JOIN = "spark_join"
    SPARK_UNION = "spark_union"
    SPARK_WRITE = "spark_write"
    SPARK_READ = "spark_read"

    # Advanced features
    ANOMALY_DETECTION = "anomaly_detection"
    QUALITY_CHECK = "quality_check"
    ALERT_TRIGGER = "alert_trigger"


@dataclass
class LineageEdge:
    """Represents a transformation edge in the lineage graph."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_node_ids: List[str] = field(default_factory=list)
    target_node_id: str = ""
    transformation_type: TransformationType = TransformationType.UNKNOWN
    operation_name: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    # Code context information
    code_context: Optional[str] = None
    file_name: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None

    # Column-level lineage information
    input_columns: Set[str] = field(default_factory=set)
    output_columns: Set[str] = field(default_factory=set)
    column_mapping: Dict[str, Set[str]] = field(
        default_factory=dict)  # output_col -> {input_cols}

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_source_node(self, node_id: str) -> None:
        """Add a source node to this edge."""
        if node_id not in self.source_node_ids:
            self.source_node_ids.append(node_id)

    def add_column_mapping(self, output_col: str, input_cols: Set[str]) -> None:
        """Add column-level lineage mapping."""
        self.output_columns.add(output_col)
        self.input_columns.update(input_cols)

        if output_col not in self.column_mapping:
            self.column_mapping[output_col] = set()
        self.column_mapping[output_col].update(input_cols)

    def get_input_columns_for_output(self, output_col: str) -> Set[str]:
        """Get input columns that contribute to a specific output column."""
        return self.column_mapping.get(output_col, set())

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary representation."""
        return {
            'id': self.id,
            'source_node_ids': self.source_node_ids,
            'target_node_id': self.target_node_id,
            'transformation_type': self.transformation_type.value,
            'operation_name': self.operation_name,
            'parameters': self.parameters,
            'created_at': self.created_at.isoformat(),
            'code_context': self.code_context,
            'file_name': self.file_name,
            'line_number': self.line_number,
            'function_name': self.function_name,
            'input_columns': list(self.input_columns),
            'output_columns': list(self.output_columns),
            'column_mapping': {k: list(v) for k, v in self.column_mapping.items()},
            'metadata': self.metadata
        }

    def __str__(self) -> str:
        return f"LineageEdge(id={self.id[:8]}, type={self.transformation_type.value}, operation={self.operation_name})"

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class ColumnLineageEdge(LineageEdge):
    """Specialized edge for column-level lineage tracking."""

    source_column: str = ""
    target_column: str = ""
    transformation_expression: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert column edge to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'source_column': self.source_column,
            'target_column': self.target_column,
            'transformation_expression': self.transformation_expression
        })
        return base_dict

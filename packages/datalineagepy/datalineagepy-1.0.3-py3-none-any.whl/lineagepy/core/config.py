"""
Configuration management for DataLineagePy.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Set
from enum import Enum


class LineageLevel(Enum):
    """Levels of lineage tracking detail."""

    NONE = "none"           # No tracking
    TABLE = "table"         # Table-level only
    COLUMN = "column"       # Column-level tracking
    FULL = "full"          # Full tracking with expressions


class VisualizationBackend(Enum):
    """Available visualization backends."""

    GRAPHVIZ = "graphviz"
    PLOTLY = "plotly"
    BOKEH = "bokeh"
    NETWORKX = "networkx"


@dataclass
class LineageConfig:
    """Configuration settings for lineage tracking."""

    # Core tracking settings
    enabled: bool = True
    tracking_level: LineageLevel = LineageLevel.COLUMN
    track_code_context: bool = True
    track_data_types: bool = True

    # Performance settings
    max_nodes: int = 50000  # Increased for better test performance
    max_edges: int = 100000  # Increased for better test performance
    enable_caching: bool = True
    cache_size: int = 1000

    # Visualization settings
    default_visualization_backend: VisualizationBackend = VisualizationBackend.GRAPHVIZ
    max_nodes_in_visualization: int = 100
    show_column_details: bool = True
    show_timestamps: bool = False

    # Output settings
    default_output_format: str = "dot"
    include_metadata_in_export: bool = True
    pretty_print_json: bool = True

    # Filtering settings
    excluded_operations: Set[str] = field(default_factory=set)
    excluded_columns: Set[str] = field(default_factory=set)
    included_operations: Optional[Set[str]] = None

    # Advanced settings
    capture_stack_trace: bool = False
    max_stack_depth: int = 5
    enable_performance_monitoring: bool = False

    # Plugin settings
    enabled_plugins: Set[str] = field(default_factory=set)
    plugin_config: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def is_operation_tracked(self, operation_name: str) -> bool:
        """Check if an operation should be tracked based on configuration."""
        if self.included_operations is not None:
            return operation_name in self.included_operations
        return operation_name not in self.excluded_operations

    def is_column_tracked(self, column_name: str) -> bool:
        """Check if a column should be tracked based on configuration."""
        return column_name not in self.excluded_columns

    def should_track_code_context(self) -> bool:
        """Check if code context should be tracked."""
        return self.track_code_context and self.enabled

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'enabled': self.enabled,
            'tracking_level': self.tracking_level.value,
            'track_code_context': self.track_code_context,
            'track_data_types': self.track_data_types,
            'max_nodes': self.max_nodes,
            'max_edges': self.max_edges,
            'enable_caching': self.enable_caching,
            'cache_size': self.cache_size,
            'default_visualization_backend': self.default_visualization_backend.value,
            'max_nodes_in_visualization': self.max_nodes_in_visualization,
            'show_column_details': self.show_column_details,
            'show_timestamps': self.show_timestamps,
            'default_output_format': self.default_output_format,
            'include_metadata_in_export': self.include_metadata_in_export,
            'pretty_print_json': self.pretty_print_json,
            'excluded_operations': list(self.excluded_operations),
            'excluded_columns': list(self.excluded_columns),
            'included_operations': list(self.included_operations) if self.included_operations else None,
            'capture_stack_trace': self.capture_stack_trace,
            'max_stack_depth': self.max_stack_depth,
            'enable_performance_monitoring': self.enable_performance_monitoring,
            'enabled_plugins': list(self.enabled_plugins),
            'plugin_config': self.plugin_config
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'LineageConfig':
        """Create configuration from dictionary."""
        config = cls()

        # Update basic fields
        for key, value in config_dict.items():
            if hasattr(config, key):
                if key == 'tracking_level':
                    setattr(config, key, LineageLevel(value))
                elif key == 'default_visualization_backend':
                    setattr(config, key, VisualizationBackend(value))
                elif key in ['excluded_operations', 'excluded_columns', 'enabled_plugins']:
                    setattr(config, key, set(value))
                elif key == 'included_operations' and value is not None:
                    setattr(config, key, set(value))
                else:
                    setattr(config, key, value)

        return config


# Global configuration instance
_global_config = LineageConfig()


def get_config() -> LineageConfig:
    """Get the global configuration instance."""
    return _global_config


def configure_lineage(**kwargs) -> None:
    """Configure global lineage settings."""
    global _global_config

    for key, value in kwargs.items():
        if hasattr(_global_config, key):
            setattr(_global_config, key, value)
        else:
            raise ValueError(f"Unknown configuration option: {key}")


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _global_config
    _global_config = LineageConfig()


# Convenience functions for common configurations
def enable_lineage_tracking() -> None:
    """Enable lineage tracking."""
    configure_lineage(enabled=True)


def disable_lineage_tracking() -> None:
    """Disable lineage tracking."""
    configure_lineage(enabled=False)


def set_tracking_level(level: LineageLevel) -> None:
    """Set the tracking level."""
    configure_lineage(tracking_level=level)


def enable_column_tracking() -> None:
    """Enable column-level tracking."""
    configure_lineage(tracking_level=LineageLevel.COLUMN)


def enable_table_tracking_only() -> None:
    """Enable only table-level tracking."""
    configure_lineage(tracking_level=LineageLevel.TABLE)

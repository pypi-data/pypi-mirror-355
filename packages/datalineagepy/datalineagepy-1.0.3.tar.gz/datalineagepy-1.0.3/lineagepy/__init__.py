"""
DataLineagePy - A lightweight Python library for tracking and visualizing data lineage
in pandas and PySpark workflows.
"""

from .testing.assertions import assert_column_lineage, assert_table_lineage
from .core.config import LineageConfig, configure_lineage
from .core.operations import register_lineage_transform
from .core.dataframe_wrapper import LineageDataFrame
from .core.tracker import LineageTracker
import logging

__version__ = "0.1.0"
__author__ = "DataLineagePy Team"
__email__ = "contact@datalineagepy.org"

logger = logging.getLogger(__name__)

# Core imports

# Testing utilities

# Visualization imports (optional dependencies)
try:
    from .visualization.graph_visualizer import LineageGraphVisualizer
    from .visualization.column_visualizer import ColumnLineageVisualizer
    from .visualization.report_generator import LineageReportGenerator
    from .visualization.exporters import (
        JSONExporter, HTMLExporter, GraphvizExporter,
        CSVExporter, MarkdownExporter
    )
    _HAS_VISUALIZATION = True
except ImportError:
    _HAS_VISUALIZATION = False

# Spark imports (optional dependencies)
try:
    from .spark.lineage_spark_dataframe import LineageSparkDataFrame
    from .spark.spark_tracker import SparkLineageTracker
    _HAS_SPARK = True
except ImportError:
    _HAS_SPARK = False

# Alerting imports (optional dependencies)
try:
    from .alerting.alert_manager import AlertManager, AlertRule, AlertSeverity
    from .alerting.monitors import PerformanceMonitor, QualityMonitor, AnomalyMonitor
    from .alerting.channels import ConsoleChannel, EmailChannel, SlackChannel
    from .alerting.rules import PerformanceRule, QualityRule, AnomalyRule, RulePresets
    _HAS_ALERTING = True
except ImportError:
    _HAS_ALERTING = False

# ML imports (optional dependencies)
try:
    from .ml.anomaly_detector import AnomalyDetector, StatisticalDetector, EnsembleDetector
    _HAS_ML = True
except ImportError:
    _HAS_ML = False

# Streaming imports (optional dependencies)
try:
    from .streaming import (
        KafkaLineageTracker, PulsarLineageTracker, KinesisLineageTracker,
        EventLineageTracker, UniversalStreamManager, LiveLineageDashboard,
        FlinkLineageTracker, KafkaStreamsTracker, StreamTestFramework,
        check_kafka_available, check_pulsar_available, check_kinesis_available,
        get_available_platforms, print_streaming_status
    )
    _HAS_STREAMING = True
except ImportError:
    _HAS_STREAMING = False

# Orchestration imports (optional dependencies) - Phase 9
try:
    from .orchestration import (
        UniversalOrchestrationManager, CrossPlatformWorkflow,
        get_available_platforms as get_orchestration_platforms,
        print_orchestration_status, get_orchestration_info
    )
    # Try to import platform-specific components (may not all be available)
    orchestration_components = {}
    try:
        from .orchestration import AirflowLineageTracker, LineageOperator, lineage_tracked
        orchestration_components.update({
            'AirflowLineageTracker': AirflowLineageTracker,
            'LineageOperator': LineageOperator,
            'lineage_tracked': lineage_tracked
        })
    except (ImportError, AttributeError):
        pass

    try:
        from .orchestration import DbtLineageTracker, DbtManifestParser
        orchestration_components.update({
            'DbtLineageTracker': DbtLineageTracker,
            'DbtManifestParser': DbtManifestParser
        })
    except (ImportError, AttributeError):
        pass

    try:
        from .orchestration import PrefectLineageTracker, lineage_tracked_flow, lineage_tracked_task
        orchestration_components.update({
            'PrefectLineageTracker': PrefectLineageTracker,
            'lineage_tracked_flow': lineage_tracked_flow,
            'lineage_tracked_task': lineage_tracked_task
        })
    except (ImportError, AttributeError):
        pass

    try:
        from .orchestration import DagsterLineageTracker, lineage_tracked_asset
        orchestration_components.update({
            'DagsterLineageTracker': DagsterLineageTracker,
            'lineage_tracked_asset': lineage_tracked_asset
        })
    except (ImportError, AttributeError):
        pass

    try:
        from .orchestration import ADFLineageTracker
        orchestration_components.update({
            'ADFLineageTracker': ADFLineageTracker
        })
    except (ImportError, AttributeError):
        pass

    _HAS_ORCHESTRATION = True
except (ImportError, AttributeError) as e:
    _HAS_ORCHESTRATION = False
    orchestration_components = {}

# Enterprise imports (optional dependencies) - Phase 10
try:
    from .enterprise import (
        is_enterprise_available, get_enterprise_status, enterprise_status_report,
        EnterpriseConfig, EnterpriseError, ClusterError, SecurityError,
        DeploymentError, TenantError
    )

    # Try to import enterprise components (may not all be available)
    enterprise_components = {}

    try:
        from .enterprise import LineageCluster, ClusterManager
        enterprise_components.update({
            'LineageCluster': LineageCluster,
            'ClusterManager': ClusterManager
        })
    except ImportError:
        pass

    try:
        from .enterprise import RBACManager, TenantManager, AuditLogger
        enterprise_components.update({
            'RBACManager': RBACManager,
            'TenantManager': TenantManager,
            'AuditLogger': AuditLogger
        })
    except ImportError:
        pass

    try:
        from .enterprise import KubernetesManager, TerraformManager, MultiCloudManager
        enterprise_components.update({
            'KubernetesManager': KubernetesManager,
            'TerraformManager': TerraformManager,
            'MultiCloudManager': MultiCloudManager
        })
    except ImportError:
        pass

    try:
        from .enterprise import OperationsManager, MonitoringManager, BackupManager
        enterprise_components.update({
            'OperationsManager': OperationsManager,
            'MonitoringManager': MonitoringManager,
            'BackupManager': BackupManager
        })
    except ImportError:
        pass

    try:
        from .enterprise import MigrationManager, EnterpriseLineageTracker
        enterprise_components.update({
            'MigrationManager': MigrationManager,
            'EnterpriseLineageTracker': EnterpriseLineageTracker
        })
    except ImportError:
        pass

    _HAS_ENTERPRISE = True
except ImportError:
    _HAS_ENTERPRISE = False
    enterprise_components = {}

# Convenience functions


def get_global_tracker():
    """Get the global lineage tracker instance."""
    return LineageTracker.get_global_instance()


# Main exports
__all__ = [
    # Core classes
    'LineageTracker',
    'LineageDataFrame',
    'LineageConfig',

    # Functions
    'register_lineage_transform',
    'configure_lineage',
    'get_global_tracker',

    # Testing
    'assert_column_lineage',
    'assert_table_lineage',

    # Version info
    '__version__',
    '__author__',
    '__email__',
]

# Add visualization exports if available
if _HAS_VISUALIZATION:
    __all__.extend([
        'LineageGraphVisualizer',
        'ColumnLineageVisualizer',
        'LineageReportGenerator',
        'JSONExporter',
        'HTMLExporter',
        'GraphvizExporter',
        'CSVExporter',
        'MarkdownExporter',
    ])

# Add Spark exports if available
if _HAS_SPARK:
    __all__.extend([
        'LineageSparkDataFrame',
        'SparkLineageTracker',
    ])

# Add alerting exports if available
if _HAS_ALERTING:
    __all__.extend([
        'AlertManager',
        'AlertRule',
        'AlertSeverity',
        'PerformanceMonitor',
        'QualityMonitor',
        'AnomalyMonitor',
        'ConsoleChannel',
        'EmailChannel',
        'SlackChannel',
        'PerformanceRule',
        'QualityRule',
        'AnomalyRule',
        'RulePresets',
    ])

# Add ML exports if available
if _HAS_ML:
    __all__.extend([
        'AnomalyDetector',
        'StatisticalDetector',
        'EnsembleDetector',
    ])

# Add streaming exports if available
if _HAS_STREAMING:
    __all__.extend([
        'KafkaLineageTracker',
        'PulsarLineageTracker',
        'KinesisLineageTracker',
        'EventLineageTracker',
        'UniversalStreamManager',
        'LiveLineageDashboard',
        'FlinkLineageTracker',
        'KafkaStreamsTracker',
        'StreamTestFramework',
        'check_kafka_available',
        'check_pulsar_available',
        'check_kinesis_available',
        'get_available_platforms',
        'print_streaming_status',
    ])

# Add orchestration exports if available
if _HAS_ORCHESTRATION:
    __all__.extend([
        'UniversalOrchestrationManager',
        'CrossPlatformWorkflow',
        'get_orchestration_platforms',
        'print_orchestration_status',
        'get_orchestration_info',
    ])
    # Add platform-specific components that are available
    __all__.extend(list(orchestration_components.keys()))

# Add enterprise exports if available
if _HAS_ENTERPRISE:
    __all__.extend([
        'is_enterprise_available',
        'get_enterprise_status',
        'enterprise_status_report',
        'EnterpriseConfig',
        'EnterpriseError',
        'ClusterError',
        'SecurityError',
        'DeploymentError',
        'TenantError',
    ])
    # Add enterprise components that are available
    __all__.extend(list(enterprise_components.keys()))

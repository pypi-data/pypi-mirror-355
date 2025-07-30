"""
DataLineagePy Orchestration Integration Module

This module provides native integration with major orchestration platforms including:
- Apache Airflow (operators, hooks, DAG lineage)
- dbt (macros, model dependencies, runs)
- Prefect (flows, tasks, deployments)
- Dagster (assets, jobs, partitions)
- Azure Data Factory (pipelines, activities)
- Universal Orchestration Management (cross-platform)
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Dependency availability flags
_HAS_AIRFLOW = False
_HAS_DBT = False
_HAS_PREFECT = False
_HAS_DAGSTER = False
_HAS_AZURE = False

# Check for optional dependencies
try:
    import airflow
    _HAS_AIRFLOW = True
except (ImportError, AttributeError) as e:
    logger.debug(
        f"Apache Airflow not available ({e}). Install with: pip install 'lineagepy[airflow]'")

try:
    import dbt
    _HAS_DBT = True
except ImportError:
    logger.debug(
        "dbt not available. Install with: pip install 'lineagepy[dbt]'")

try:
    import prefect
    _HAS_PREFECT = True
except ImportError:
    logger.debug(
        "Prefect not available. Install with: pip install 'lineagepy[prefect]'")

try:
    import dagster
    _HAS_DAGSTER = True
except ImportError:
    logger.debug(
        "Dagster not available. Install with: pip install 'lineagepy[dagster]'")

try:
    import azure.mgmt.datafactory
    _HAS_AZURE = True
except ImportError:
    logger.debug(
        "Azure SDK not available. Install with: pip install 'lineagepy[azure]'")

# Conditional imports based on availability
if _HAS_AIRFLOW:
    try:
        from .airflow_lineage import AirflowLineageTracker, LineageOperator, LineageHook, lineage_tracked
        __all_airflow__ = ['AirflowLineageTracker',
                           'LineageOperator', 'LineageHook', 'lineage_tracked']
    except ImportError as e:
        logger.warning(f"Failed to import Airflow components: {e}")
        __all_airflow__ = []
else:
    __all_airflow__ = []

if _HAS_DBT:
    try:
        from .dbt_lineage import DbtLineageTracker, DbtManifestParser, dbt_lineage_macro
        __all_dbt__ = ['DbtLineageTracker',
                       'DbtManifestParser', 'dbt_lineage_macro']
    except ImportError as e:
        logger.warning(f"Failed to import dbt components: {e}")
        __all_dbt__ = []
else:
    __all_dbt__ = []

if _HAS_PREFECT:
    try:
        from .prefect_lineage import PrefectLineageTracker, lineage_tracked_flow, lineage_tracked_task
        __all_prefect__ = ['PrefectLineageTracker',
                           'lineage_tracked_flow', 'lineage_tracked_task']
    except ImportError as e:
        logger.warning(f"Failed to import Prefect components: {e}")
        __all_prefect__ = []
else:
    __all_prefect__ = []

if _HAS_DAGSTER:
    try:
        from .dagster_lineage import DagsterLineageTracker, lineage_tracked_asset, dagster_lineage_resource
        __all_dagster__ = ['DagsterLineageTracker',
                           'lineage_tracked_asset', 'dagster_lineage_resource']
    except ImportError as e:
        logger.warning(f"Failed to import Dagster components: {e}")
        __all_dagster__ = []
else:
    __all_dagster__ = []

if _HAS_AZURE:
    try:
        from .adf_lineage import ADFLineageTracker, ADFPipelineTracker
        __all_azure__ = ['ADFLineageTracker', 'ADFPipelineTracker']
    except ImportError as e:
        logger.warning(f"Failed to import Azure Data Factory components: {e}")
        __all_azure__ = []
else:
    __all_azure__ = []

# Universal orchestration manager (always available)
try:
    from .universal_orchestration import UniversalOrchestrationManager, CrossPlatformWorkflow
    __all_universal__ = [
        'UniversalOrchestrationManager', 'CrossPlatformWorkflow']
except ImportError as e:
    logger.warning(f"Failed to import Universal Orchestration components: {e}")
    __all_universal__ = []

# Testing framework (always available)
try:
    from .testing import OrchestrationTestFramework, WorkflowTester
    __all_testing__ = ['OrchestrationTestFramework', 'WorkflowTester']
except ImportError as e:
    logger.warning(f"Failed to import Orchestration Testing components: {e}")
    __all_testing__ = []


def check_airflow_available() -> bool:
    """Check if Apache Airflow is available."""
    return _HAS_AIRFLOW


def check_dbt_available() -> bool:
    """Check if dbt is available."""
    return _HAS_DBT


def check_prefect_available() -> bool:
    """Check if Prefect is available."""
    return _HAS_PREFECT


def check_dagster_available() -> bool:
    """Check if Dagster is available."""
    return _HAS_DAGSTER


def check_azure_available() -> bool:
    """Check if Azure SDK is available."""
    return _HAS_AZURE


def get_available_platforms() -> List[str]:
    """Get list of available orchestration platforms."""
    platforms = []
    if _HAS_AIRFLOW:
        platforms.append('airflow')
    if _HAS_DBT:
        platforms.append('dbt')
    if _HAS_PREFECT:
        platforms.append('prefect')
    if _HAS_DAGSTER:
        platforms.append('dagster')
    if _HAS_AZURE:
        platforms.append('azure')
    platforms.append('universal')  # Always available
    return platforms


def print_orchestration_status() -> None:
    """Print the status of orchestration platform availability."""
    print("DataLineagePy Orchestration Platform Status:")
    print("=" * 50)

    platforms = [
        ('Apache Airflow', _HAS_AIRFLOW, 'lineagepy[airflow]'),
        ('dbt', _HAS_DBT, 'lineagepy[dbt]'),
        ('Prefect', _HAS_PREFECT, 'lineagepy[prefect]'),
        ('Dagster', _HAS_DAGSTER, 'lineagepy[dagster]'),
        ('Azure Data Factory', _HAS_AZURE, 'lineagepy[azure]'),
        ('Universal Manager', True, 'Built-in'),
        ('Testing Framework', True, 'Built-in'),
    ]

    for name, available, install_cmd in platforms:
        status = "✅ Available" if available else "❌ Not Available"
        print(f"{name:<20} {status:<15} {install_cmd}")

    print("\nTo install all orchestration dependencies:")
    print("pip install 'lineagepy[orchestration-full]'")


def get_orchestration_info() -> Dict[str, Any]:
    """Get detailed orchestration platform information."""
    return {
        'platforms': {
            'airflow': {
                'available': _HAS_AIRFLOW,
                'version': getattr(__import__('airflow', fromlist=['']), '__version__', None) if _HAS_AIRFLOW else None,
                'components': __all_airflow__
            },
            'dbt': {
                'available': _HAS_DBT,
                'version': getattr(__import__('dbt', fromlist=['']), '__version__', None) if _HAS_DBT else None,
                'components': __all_dbt__
            },
            'prefect': {
                'available': _HAS_PREFECT,
                'version': getattr(__import__('prefect', fromlist=['']), '__version__', None) if _HAS_PREFECT else None,
                'components': __all_prefect__
            },
            'dagster': {
                'available': _HAS_DAGSTER,
                'version': getattr(__import__('dagster', fromlist=['']), '__version__', None) if _HAS_DAGSTER else None,
                'components': __all_dagster__
            },
            'azure': {
                'available': _HAS_AZURE,
                'version': getattr(__import__('azure.mgmt.datafactory', fromlist=['']), '__version__', None) if _HAS_AZURE else None,
                'components': __all_azure__
            },
            'universal': {
                'available': True,
                'version': 'Built-in',
                'components': __all_universal__
            },
            'testing': {
                'available': True,
                'version': 'Built-in',
                'components': __all_testing__
            }
        },
        'total_platforms': len(get_available_platforms()),
        'enterprise_ready': _HAS_AIRFLOW and _HAS_DBT and _HAS_PREFECT,
        'recommendations': _get_recommendations()
    }


def _get_recommendations() -> List[str]:
    """Get recommendations for missing platforms."""
    recommendations = []

    if not _HAS_AIRFLOW:
        recommendations.append(
            "Install Apache Airflow for DAG lineage: pip install 'lineagepy[airflow]'")
    if not _HAS_DBT:
        recommendations.append(
            "Install dbt for model lineage: pip install 'lineagepy[dbt]'")
    if not _HAS_PREFECT:
        recommendations.append(
            "Install Prefect for flow lineage: pip install 'lineagepy[prefect]'")
    if not _HAS_DAGSTER:
        recommendations.append(
            "Install Dagster for asset lineage: pip install 'lineagepy[dagster]'")
    if not _HAS_AZURE:
        recommendations.append(
            "Install Azure SDK for ADF lineage: pip install 'lineagepy[azure]'")

    if not recommendations:
        recommendations.append(
            "All major orchestration platforms are available! 🎉")

    return recommendations


# Export available components
__all__ = (
    __all_airflow__ +
    __all_dbt__ +
    __all_prefect__ +
    __all_dagster__ +
    __all_azure__ +
    __all_universal__ +
    __all_testing__ +
    [
        'check_airflow_available',
        'check_dbt_available',
        'check_prefect_available',
        'check_dagster_available',
        'check_azure_available',
        'get_available_platforms',
        'print_orchestration_status',
        'get_orchestration_info'
    ]
)

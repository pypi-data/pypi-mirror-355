"""
DataLineagePy Enterprise Scale & Cloud Native Integration

This module provides enterprise-grade features including:
- Distributed cluster management
- Multi-tenant architecture
- Enterprise security and RBAC
- Cloud-native deployment capabilities
- High availability and monitoring

Enterprise features require additional dependencies and are designed
for production deployments with petabyte-scale lineage requirements.
"""

import logging
import warnings
from typing import Dict, List, Optional, Any

# Core enterprise components - always available
from .config import EnterpriseConfig
from .exceptions import (
    EnterpriseError,
    ClusterError,
    SecurityError,
    DeploymentError,
    TenantError
)

# Initialize enterprise logger
logger = logging.getLogger(__name__)

# Track availability of enterprise components
_ENTERPRISE_AVAILABLE = {}

# Cluster Management
try:
    from .cluster import (
        LineageCluster,
        ClusterManager,
        DistributedStorage,
        LoadBalancer,
        HealthMonitor
    )
    _ENTERPRISE_AVAILABLE['cluster'] = True
except ImportError as e:
    logger.debug(f"Cluster management not available: {e}")
    _ENTERPRISE_AVAILABLE['cluster'] = False

    # Provide mock implementations for development
    class LineageCluster:
        def __init__(self, *args, **kwargs):
            raise EnterpriseError(
                "Cluster management requires enterprise dependencies. "
                "Install with: pip install data-lineage-py[enterprise-cluster]"
            )

# Security and RBAC
try:
    from .security import (
        RBACManager,
        TenantManager,
        AuditLogger,
        EncryptionManager,
        SecurityPolicy
    )
    _ENTERPRISE_AVAILABLE['security'] = True
except ImportError as e:
    logger.debug(f"Enterprise security not available: {e}")
    _ENTERPRISE_AVAILABLE['security'] = False

    class RBACManager:
        def __init__(self, *args, **kwargs):
            raise EnterpriseError(
                "Enterprise security requires additional dependencies. "
                "Install with: pip install data-lineage-py[enterprise-security]"
            )

    class TenantManager:
        def __init__(self, *args, **kwargs):
            raise EnterpriseError(
                "Multi-tenancy requires enterprise dependencies. "
                "Install with: pip install data-lineage-py[enterprise-security]"
            )

# Deployment and Infrastructure
try:
    from .deployment import (
        KubernetesManager,
        TerraformManager,
        CloudConfigManager,
        MultiCloudManager,
        HelmChartManager
    )
    _ENTERPRISE_AVAILABLE['deployment'] = True
except ImportError as e:
    logger.debug(f"Deployment management not available: {e}")
    _ENTERPRISE_AVAILABLE['deployment'] = False

    class KubernetesManager:
        def __init__(self, *args, **kwargs):
            raise EnterpriseError(
                "Kubernetes deployment requires additional dependencies. "
                "Install with: pip install data-lineage-py[enterprise-k8s]"
            )

# Operations and Monitoring
try:
    from .operations import (
        OperationsManager,
        MonitoringManager,
        BackupManager,
        MaintenanceManager,
        AlertManager
    )
    _ENTERPRISE_AVAILABLE['operations'] = True
except ImportError as e:
    logger.debug(f"Enterprise operations not available: {e}")
    _ENTERPRISE_AVAILABLE['operations'] = False

    class OperationsManager:
        def __init__(self, *args, **kwargs):
            raise EnterpriseError(
                "Enterprise operations requires additional dependencies. "
                "Install with: pip install data-lineage-py[enterprise-ops]"
            )

# Migration and Utilities
try:
    from .migration import (
        MigrationManager,
        EnterpriseLineageTracker,
        ScalabilityAnalyzer,
        PerformanceOptimizer
    )
    _ENTERPRISE_AVAILABLE['migration'] = True
except ImportError as e:
    logger.debug(f"Enterprise migration not available: {e}")
    _ENTERPRISE_AVAILABLE['migration'] = False

    class MigrationManager:
        def __init__(self, *args, **kwargs):
            raise EnterpriseError(
                "Migration tools require enterprise dependencies. "
                "Install with: pip install data-lineage-py[enterprise-migration]"
            )


def is_enterprise_available() -> bool:
    """Check if any enterprise features are available."""
    return any(_ENTERPRISE_AVAILABLE.values())


def get_enterprise_status() -> Dict[str, bool]:
    """Get detailed status of enterprise component availability."""
    return _ENTERPRISE_AVAILABLE.copy()


def get_missing_enterprise_components() -> List[str]:
    """Get list of missing enterprise components."""
    return [
        component for component, available
        in _ENTERPRISE_AVAILABLE.items()
        if not available
    ]


def check_enterprise_requirements(components: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Check enterprise requirements and provide installation guidance.

    Args:
        components: Specific components to check, or None for all

    Returns:
        Dictionary with status and recommendations
    """
    if components is None:
        components = list(_ENTERPRISE_AVAILABLE.keys())

    status = {}
    missing = []
    recommendations = []

    for component in components:
        if component in _ENTERPRISE_AVAILABLE:
            status[component] = _ENTERPRISE_AVAILABLE[component]
            if not _ENTERPRISE_AVAILABLE[component]:
                missing.append(component)
        else:
            status[component] = False
            missing.append(component)

    # Generate installation recommendations
    if 'cluster' in missing:
        recommendations.append(
            "pip install data-lineage-py[enterprise-cluster] - For distributed cluster management"
        )
    if 'security' in missing:
        recommendations.append(
            "pip install data-lineage-py[enterprise-security] - For RBAC and multi-tenancy"
        )
    if 'deployment' in missing:
        recommendations.append(
            "pip install data-lineage-py[enterprise-k8s] - For Kubernetes deployment"
        )
    if 'operations' in missing:
        recommendations.append(
            "pip install data-lineage-py[enterprise-ops] - For monitoring and operations"
        )
    if len(missing) > 2:
        recommendations.append(
            "pip install data-lineage-py[enterprise-full] - For all enterprise features"
        )

    return {
        'status': status,
        'missing_components': missing,
        'available_components': [c for c in components if status.get(c, False)],
        'recommendations': recommendations,
        'enterprise_ready': len(missing) == 0
    }


def enterprise_status_report() -> str:
    """Generate a comprehensive enterprise status report."""
    status = check_enterprise_requirements()

    report = ["🏢 DataLineagePy Enterprise Status Report", "=" * 50]

    # Overall status
    if status['enterprise_ready']:
        report.append("✅ Enterprise features: FULLY AVAILABLE")
    else:
        report.append("⚠️  Enterprise features: PARTIALLY AVAILABLE")

    report.append("")

    # Component status
    report.append("Component Availability:")
    for component, available in status['status'].items():
        emoji = "✅" if available else "❌"
        report.append(
            f"  {emoji} {component.title()}: {'Available' if available else 'Missing'}")

    # Recommendations
    if status['recommendations']:
        report.append("\nInstallation Recommendations:")
        for rec in status['recommendations']:
            report.append(f"  • {rec}")

    # Enterprise capabilities
    report.append("\nEnterprise Capabilities:")
    capabilities = [
        ("Distributed Clusters", "cluster"),
        ("Multi-Tenant Security", "security"),
        ("Cloud-Native Deployment", "deployment"),
        ("Production Operations", "operations"),
        ("Enterprise Migration", "migration")
    ]

    for capability, component in capabilities:
        available = status['status'].get(component, False)
        emoji = "🟢" if available else "🔴"
        report.append(f"  {emoji} {capability}")

    if not status['enterprise_ready']:
        report.append(
            "\n💡 Install missing components to unlock full enterprise capabilities.")

    return "\n".join(report)


# Issue warnings for missing critical enterprise dependencies
if not is_enterprise_available():
    warnings.warn(
        "Enterprise features are not fully available. "
        "Install enterprise dependencies for production deployments.",
        UserWarning,
        stacklevel=2
    )

# Export main enterprise classes and functions
__all__ = [
    # Core
    'EnterpriseConfig',
    'EnterpriseError',
    'ClusterError',
    'SecurityError',
    'DeploymentError',
    'TenantError',

    # Cluster Management
    'LineageCluster',
    'ClusterManager',
    'DistributedStorage',
    'LoadBalancer',
    'HealthMonitor',

    # Security
    'RBACManager',
    'TenantManager',
    'AuditLogger',
    'EncryptionManager',
    'SecurityPolicy',

    # Deployment
    'KubernetesManager',
    'TerraformManager',
    'CloudConfigManager',
    'MultiCloudManager',
    'HelmChartManager',

    # Operations
    'OperationsManager',
    'MonitoringManager',
    'BackupManager',
    'MaintenanceManager',
    'AlertManager',

    # Migration
    'MigrationManager',
    'EnterpriseLineageTracker',
    'ScalabilityAnalyzer',
    'PerformanceOptimizer',

    # Utilities
    'is_enterprise_available',
    'get_enterprise_status',
    'get_missing_enterprise_components',
    'check_enterprise_requirements',
    'enterprise_status_report',
]

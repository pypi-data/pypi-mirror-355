"""
Enterprise Exception Classes

Comprehensive exception hierarchy for enterprise-grade error handling
with proper categorization, error codes, and recovery suggestions.
"""

from typing import Optional, Dict, Any, List


class EnterpriseError(Exception):
    """Base exception class for all enterprise-related errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.error_code = error_code or "ENT_GENERAL_ERROR"
        self.details = details or {}
        self.recovery_suggestions = recovery_suggestions or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/reporting."""
        return {
            'error_type': self.__class__.__name__,
            'message': str(self),
            'error_code': self.error_code,
            'details': self.details,
            'recovery_suggestions': self.recovery_suggestions
        }


class ClusterError(EnterpriseError):
    """Exceptions related to distributed cluster operations."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        if not self.error_code.startswith('CLUSTER_'):
            self.error_code = f"CLUSTER_{self.error_code}"


class ClusterNodeError(ClusterError):
    """Exceptions related to individual cluster nodes."""

    def __init__(self, message: str, node_id: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.node_id = node_id
        if node_id:
            self.details['node_id'] = node_id


class ClusterQuorumError(ClusterError):
    """Exceptions when cluster loses quorum."""

    def __init__(self, message: str, active_nodes: int, required_nodes: int, **kwargs):
        super().__init__(message, **kwargs)
        self.active_nodes = active_nodes
        self.required_nodes = required_nodes
        self.details.update({
            'active_nodes': active_nodes,
            'required_nodes': required_nodes
        })
        self.recovery_suggestions.extend([
            "Check network connectivity between cluster nodes",
            "Verify cluster node health status",
            "Consider adding more nodes to restore quorum"
        ])


class ClusterSplitBrainError(ClusterError):
    """Exceptions when cluster experiences split-brain scenario."""

    def __init__(self, message: str, partitions: List[List[str]], **kwargs):
        super().__init__(message, **kwargs)
        self.partitions = partitions
        self.details['partitions'] = partitions
        self.recovery_suggestions.extend([
            "Identify the partition with the most recent data",
            "Manually resolve split-brain by shutting down minority partitions",
            "Review network partitioning issues"
        ])


class SecurityError(EnterpriseError):
    """Exceptions related to enterprise security and authentication."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        if not self.error_code.startswith('SECURITY_'):
            self.error_code = f"SECURITY_{self.error_code}"


class AuthenticationError(SecurityError):
    """Exceptions related to user authentication."""

    def __init__(self, message: str, user_id: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.user_id = user_id
        if user_id:
            self.details['user_id'] = user_id
        self.recovery_suggestions.extend([
            "Verify user credentials",
            "Check authentication provider connectivity",
            "Review user account status"
        ])


class AuthorizationError(SecurityError):
    """Exceptions related to user authorization."""

    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.user_id = user_id
        self.resource = resource
        self.action = action
        self.details.update({
            'user_id': user_id,
            'resource': resource,
            'action': action
        })
        self.recovery_suggestions.extend([
            "Review user role assignments",
            "Check resource permissions",
            "Contact administrator for access"
        ])


class TenantError(EnterpriseError):
    """Exceptions related to multi-tenant operations."""

    def __init__(self, message: str, tenant_id: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.tenant_id = tenant_id
        if tenant_id:
            self.details['tenant_id'] = tenant_id
        if not self.error_code.startswith('TENANT_'):
            self.error_code = f"TENANT_{self.error_code}"


class TenantQuotaExceededError(TenantError):
    """Exceptions when tenant exceeds resource quotas."""

    def __init__(
        self,
        message: str,
        tenant_id: str,
        quota_type: str,
        current_usage: Any,
        quota_limit: Any,
        **kwargs
    ):
        super().__init__(message, tenant_id=tenant_id, **kwargs)
        self.quota_type = quota_type
        self.current_usage = current_usage
        self.quota_limit = quota_limit
        self.details.update({
            'quota_type': quota_type,
            'current_usage': current_usage,
            'quota_limit': quota_limit
        })
        self.recovery_suggestions.extend([
            f"Reduce {quota_type} usage",
            "Request quota increase from administrator",
            "Review and cleanup unused resources"
        ])


class TenantIsolationError(TenantError):
    """Exceptions related to tenant data isolation."""

    def __init__(
        self,
        message: str,
        tenant_id: str,
        isolation_breach_type: str,
        **kwargs
    ):
        super().__init__(message, tenant_id=tenant_id, **kwargs)
        self.isolation_breach_type = isolation_breach_type
        self.details['isolation_breach_type'] = isolation_breach_type
        self.recovery_suggestions.extend([
            "Review tenant isolation configuration",
            "Audit data access patterns",
            "Contact security team immediately"
        ])


class DeploymentError(EnterpriseError):
    """Exceptions related to deployment and infrastructure."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        if not self.error_code.startswith('DEPLOY_'):
            self.error_code = f"DEPLOY_{self.error_code}"


class KubernetesError(DeploymentError):
    """Exceptions related to Kubernetes operations."""

    def __init__(
        self,
        message: str,
        namespace: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.namespace = namespace
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.details.update({
            'namespace': namespace,
            'resource_type': resource_type,
            'resource_name': resource_name
        })


class CloudProviderError(DeploymentError):
    """Exceptions related to cloud provider operations."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        region: Optional[str] = None,
        service: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.provider = provider
        self.region = region
        self.service = service
        self.details.update({
            'provider': provider,
            'region': region,
            'service': service
        })


class OperationsError(EnterpriseError):
    """Exceptions related to operational activities."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        if not self.error_code.startswith('OPS_'):
            self.error_code = f"OPS_{self.error_code}"


class BackupError(OperationsError):
    """Exceptions related to backup operations."""

    def __init__(
        self,
        message: str,
        backup_id: Optional[str] = None,
        backup_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.backup_id = backup_id
        self.backup_type = backup_type
        self.details.update({
            'backup_id': backup_id,
            'backup_type': backup_type
        })


class MonitoringError(OperationsError):
    """Exceptions related to monitoring and alerting."""

    def __init__(
        self,
        message: str,
        metric_name: Optional[str] = None,
        alert_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.metric_name = metric_name
        self.alert_name = alert_name
        self.details.update({
            'metric_name': metric_name,
            'alert_name': alert_name
        })


class ScalabilityError(EnterpriseError):
    """Exceptions related to scalability limits."""

    def __init__(
        self,
        message: str,
        limit_type: str,
        current_value: Any,
        max_value: Any,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.limit_type = limit_type
        self.current_value = current_value
        self.max_value = max_value
        self.details.update({
            'limit_type': limit_type,
            'current_value': current_value,
            'max_value': max_value
        })
        self.recovery_suggestions.extend([
            f"Scale up {limit_type} capacity",
            "Optimize resource usage",
            "Consider architectural changes"
        ])


class PerformanceError(EnterpriseError):
    """Exceptions related to performance issues."""

    def __init__(
        self,
        message: str,
        operation: str,
        duration_ms: Optional[float] = None,
        threshold_ms: Optional[float] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.operation = operation
        self.duration_ms = duration_ms
        self.threshold_ms = threshold_ms
        self.details.update({
            'operation': operation,
            'duration_ms': duration_ms,
            'threshold_ms': threshold_ms
        })
        self.recovery_suggestions.extend([
            "Review query optimization",
            "Check system resources",
            "Consider adding more nodes"
        ])


class ComplianceError(SecurityError):
    """Exceptions related to compliance violations."""

    def __init__(
        self,
        message: str,
        compliance_framework: str,
        violation_type: str,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.compliance_framework = compliance_framework
        self.violation_type = violation_type
        self.details.update({
            'compliance_framework': compliance_framework,
            'violation_type': violation_type
        })
        self.recovery_suggestions.extend([
            f"Review {compliance_framework} requirements",
            "Contact compliance team",
            "Implement required controls"
        ])


class ConfigurationError(EnterpriseError):
    """Exceptions related to configuration issues."""

    def __init__(
        self,
        message: str,
        config_section: Optional[str] = None,
        config_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.config_section = config_section
        self.config_key = config_key
        self.details.update({
            'config_section': config_section,
            'config_key': config_key
        })
        self.recovery_suggestions.extend([
            "Review configuration file",
            "Check environment variables",
            "Validate configuration against schema"
        ])


class MigrationError(EnterpriseError):
    """Exceptions related to data migration operations."""

    def __init__(
        self,
        message: str,
        migration_id: Optional[str] = None,
        source_version: Optional[str] = None,
        target_version: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.migration_id = migration_id
        self.source_version = source_version
        self.target_version = target_version
        self.details.update({
            'migration_id': migration_id,
            'source_version': source_version,
            'target_version': target_version
        })
        self.recovery_suggestions.extend([
            "Review migration logs",
            "Verify data integrity",
            "Consider rollback if necessary"
        ])


# Exception mapping for error code categorization
ERROR_CODE_MAPPING = {
    'CLUSTER_NODE_UNREACHABLE': ClusterNodeError,
    'CLUSTER_QUORUM_LOST': ClusterQuorumError,
    'CLUSTER_SPLIT_BRAIN': ClusterSplitBrainError,
    'SECURITY_AUTH_FAILED': AuthenticationError,
    'SECURITY_AUTHZ_DENIED': AuthorizationError,
    'TENANT_QUOTA_EXCEEDED': TenantQuotaExceededError,
    'TENANT_ISOLATION_BREACH': TenantIsolationError,
    'DEPLOY_K8S_FAILURE': KubernetesError,
    'DEPLOY_CLOUD_FAILURE': CloudProviderError,
    'OPS_BACKUP_FAILED': BackupError,
    'OPS_MONITORING_FAILURE': MonitoringError,
    'SCALABILITY_LIMIT_REACHED': ScalabilityError,
    'PERFORMANCE_THRESHOLD_EXCEEDED': PerformanceError,
    'COMPLIANCE_VIOLATION': ComplianceError,
    'CONFIG_INVALID': ConfigurationError,
    'MIGRATION_FAILED': MigrationError,
}


def create_enterprise_exception(
    error_code: str,
    message: str,
    **kwargs
) -> EnterpriseError:
    """
    Factory function to create appropriate exception based on error code.

    Args:
        error_code: Standard enterprise error code
        message: Error message
        **kwargs: Additional exception-specific parameters

    Returns:
        Appropriate exception instance
    """
    exception_class = ERROR_CODE_MAPPING.get(error_code, EnterpriseError)
    return exception_class(message, error_code=error_code, **kwargs)


def handle_enterprise_exception(
    exception: EnterpriseError,
    logger,
    include_recovery_suggestions: bool = True
) -> None:
    """
    Standard enterprise exception handler with logging and reporting.

    Args:
        exception: Enterprise exception to handle
        logger: Logger instance for reporting
        include_recovery_suggestions: Whether to log recovery suggestions
    """
    # Log the exception with full details
    error_dict = exception.to_dict()
    logger.error(
        f"Enterprise Error [{exception.error_code}]: {exception}",
        extra=error_dict
    )

    # Log recovery suggestions if available and requested
    if include_recovery_suggestions and exception.recovery_suggestions:
        logger.info("Recovery suggestions:")
        for i, suggestion in enumerate(exception.recovery_suggestions, 1):
            logger.info(f"  {i}. {suggestion}")

    # Additional handling based on exception type
    if isinstance(exception, (ClusterQuorumError, ClusterSplitBrainError)):
        logger.critical(
            "Critical cluster issue detected - immediate attention required")
    elif isinstance(exception, (TenantIsolationError, ComplianceError)):
        logger.critical(
            "Security/compliance issue detected - alerting security team")
    elif isinstance(exception, PerformanceError):
        logger.warning(
            "Performance degradation detected - monitoring required")

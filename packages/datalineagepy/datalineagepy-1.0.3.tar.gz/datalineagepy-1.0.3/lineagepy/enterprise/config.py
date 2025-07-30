"""
Enterprise Configuration Management

Centralized configuration system for enterprise deployments with support for:
- Multi-environment configurations (dev, staging, prod)
- Security policy management
- Cluster and deployment settings
- Performance tuning parameters
- Compliance and audit configurations
"""

import os
import json
import yaml
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClusterConfig:
    """Configuration for distributed cluster deployment."""
    name: str = "lineagepy-cluster"
    nodes: List[str] = field(default_factory=list)
    replication_factor: int = 3
    storage_backend: str = "postgresql"
    sharding_strategy: str = "consistent_hash"
    max_nodes: int = 1000000
    max_storage_gb: int = 10000
    auto_scaling: bool = True
    health_check_interval: int = 30
    failover_timeout: int = 300
    load_balancer_type: str = "round_robin"


@dataclass
class SecurityConfig:
    """Configuration for enterprise security and compliance."""
    authentication_provider: str = "ldap"
    mfa_required: bool = True
    session_timeout_minutes: int = 480  # 8 hours
    password_policy: Dict[str, Any] = field(default_factory=lambda: {
        "min_length": 12,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_symbols": True,
        "max_age_days": 90
    })
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
    audit_logging: bool = True
    audit_retention_days: int = 2555  # 7 years
    compliance_frameworks: List[str] = field(
        default_factory=lambda: ["SOC2", "GDPR"])
    rbac_enabled: bool = True
    tenant_isolation: str = "strict"


@dataclass
class DeploymentConfig:
    """Configuration for cloud-native deployment."""
    platform: str = "kubernetes"
    cloud_provider: str = "aws"
    region: str = "us-west-2"
    availability_zones: List[str] = field(
        default_factory=lambda: ["us-west-2a", "us-west-2b", "us-west-2c"])
    instance_type: str = "r5.2xlarge"
    min_instances: int = 3
    max_instances: int = 20
    storage_class: str = "gp3"
    backup_enabled: bool = True
    backup_retention_days: int = 30
    monitoring_enabled: bool = True
    logging_enabled: bool = True
    auto_update: bool = False


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization."""
    query_timeout_ms: int = 5000
    cache_enabled: bool = True
    cache_size_mb: int = 1024
    cache_ttl_seconds: int = 3600
    parallel_queries: bool = True
    max_concurrent_queries: int = 100
    connection_pool_size: int = 20
    batch_size: int = 10000
    compression_enabled: bool = True
    compression_algorithm: str = "zstd"


@dataclass
class TenantConfig:
    """Configuration for multi-tenant settings."""
    default_tier: str = "standard"
    isolation_level: str = "strict"
    resource_quotas: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "starter": {
            "max_nodes": 10000,
            "max_storage_gb": 10,
            "api_calls_per_hour": 1000,
            "max_users": 5
        },
        "professional": {
            "max_nodes": 100000,
            "max_storage_gb": 100,
            "api_calls_per_hour": 10000,
            "max_users": 50
        },
        "enterprise": {
            "max_nodes": 1000000,
            "max_storage_gb": 1000,
            "api_calls_per_hour": 100000,
            "max_users": 500
        }
    })
    billing_enabled: bool = True
    usage_tracking: bool = True


class EnterpriseConfig:
    """
    Centralized enterprise configuration management system.

    Supports multiple environments, secure configuration storage,
    and runtime configuration updates.
    """

    def __init__(
        self,
        environment: str = "production",
        config_file: Optional[Union[str, Path]] = None,
        config_dict: Optional[Dict[str, Any]] = None
    ):
        self.environment = environment
        self._config_file = config_file
        self._config = self._load_configuration(config_dict)

        # Initialize component configurations
        self.cluster = ClusterConfig(**self._config.get('cluster', {}))
        self.security = SecurityConfig(**self._config.get('security', {}))
        self.deployment = DeploymentConfig(
            **self._config.get('deployment', {}))
        self.performance = PerformanceConfig(
            **self._config.get('performance', {}))
        self.tenant = TenantConfig(**self._config.get('tenant', {}))

        logger.info(
            f"Enterprise configuration loaded for environment: {environment}")

    def _load_configuration(self, config_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Load configuration from various sources with precedence."""
        config = {}

        # 1. Load default configuration
        config.update(self._get_default_config())

        # 2. Load environment-specific configuration file
        if self._config_file:
            config.update(self._load_from_file(self._config_file))
        else:
            # Try to find environment-specific config files
            config_paths = [
                f"enterprise-{self.environment}.yaml",
                f"enterprise-{self.environment}.yml",
                f"enterprise-{self.environment}.json",
                "enterprise.yaml",
                "enterprise.yml",
                "enterprise.json"
            ]

            for config_path in config_paths:
                if os.path.exists(config_path):
                    config.update(self._load_from_file(config_path))
                    break

        # 3. Load from environment variables
        config.update(self._load_from_env())

        # 4. Override with provided dictionary
        if config_dict:
            config.update(config_dict)

        return config

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default enterprise configuration."""
        return {
            'cluster': asdict(ClusterConfig()),
            'security': asdict(SecurityConfig()),
            'deployment': asdict(DeploymentConfig()),
            'performance': asdict(PerformanceConfig()),
            'tenant': asdict(TenantConfig())
        }

    def _load_from_file(self, config_file: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file."""
        config_path = Path(config_file)

        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return {}

        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif config_path.suffix.lower() == '.json':
                    return json.load(f) or {}
                else:
                    logger.warning(
                        f"Unsupported config file format: {config_path}")
                    return {}
        except Exception as e:
            logger.error(
                f"Error loading configuration file {config_path}: {e}")
            return {}

    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}

        # Cluster configuration
        if os.getenv('LINEAGEPY_CLUSTER_NAME'):
            config.setdefault('cluster', {})['name'] = os.getenv(
                'LINEAGEPY_CLUSTER_NAME')
        if os.getenv('LINEAGEPY_CLUSTER_NODES'):
            config.setdefault('cluster', {})['nodes'] = os.getenv(
                'LINEAGEPY_CLUSTER_NODES').split(',')
        if os.getenv('LINEAGEPY_STORAGE_BACKEND'):
            config.setdefault('cluster', {})['storage_backend'] = os.getenv(
                'LINEAGEPY_STORAGE_BACKEND')

        # Security configuration
        if os.getenv('LINEAGEPY_AUTH_PROVIDER'):
            config.setdefault('security', {})['authentication_provider'] = os.getenv(
                'LINEAGEPY_AUTH_PROVIDER')
        if os.getenv('LINEAGEPY_MFA_REQUIRED'):
            config.setdefault('security', {})['mfa_required'] = os.getenv(
                'LINEAGEPY_MFA_REQUIRED').lower() == 'true'

        # Deployment configuration
        if os.getenv('LINEAGEPY_CLOUD_PROVIDER'):
            config.setdefault('deployment', {})['cloud_provider'] = os.getenv(
                'LINEAGEPY_CLOUD_PROVIDER')
        if os.getenv('LINEAGEPY_REGION'):
            config.setdefault('deployment', {})[
                'region'] = os.getenv('LINEAGEPY_REGION')
        if os.getenv('LINEAGEPY_INSTANCE_TYPE'):
            config.setdefault('deployment', {})['instance_type'] = os.getenv(
                'LINEAGEPY_INSTANCE_TYPE')

        return config

    def get_config(self, section: str, key: Optional[str] = None) -> Any:
        """Get configuration value for a specific section and key."""
        section_config = getattr(self, section, None)
        if section_config is None:
            raise ValueError(f"Unknown configuration section: {section}")

        if key is None:
            return section_config

        return getattr(section_config, key, None)

    def update_config(self, section: str, updates: Dict[str, Any]) -> None:
        """Update configuration for a specific section."""
        section_config = getattr(self, section, None)
        if section_config is None:
            raise ValueError(f"Unknown configuration section: {section}")

        for key, value in updates.items():
            if hasattr(section_config, key):
                setattr(section_config, key, value)
            else:
                logger.warning(
                    f"Unknown configuration key {key} in section {section}")

        logger.info(f"Updated {section} configuration: {updates}")

    def validate_config(self) -> Dict[str, List[str]]:
        """Validate enterprise configuration and return any issues."""
        issues = {}

        # Validate cluster configuration
        cluster_issues = []
        if not self.cluster.nodes and self.cluster.name != "single-node":
            cluster_issues.append(
                "No cluster nodes specified for distributed deployment")
        if self.cluster.replication_factor < 1:
            cluster_issues.append("Replication factor must be at least 1")
        if self.cluster.replication_factor > len(self.cluster.nodes) and self.cluster.nodes:
            cluster_issues.append(
                "Replication factor cannot exceed number of nodes")
        if cluster_issues:
            issues['cluster'] = cluster_issues

        # Validate security configuration
        security_issues = []
        if not self.security.encryption_at_rest and "HIPAA" in self.security.compliance_frameworks:
            security_issues.append(
                "HIPAA compliance requires encryption at rest")
        if not self.security.audit_logging and "SOC2" in self.security.compliance_frameworks:
            security_issues.append("SOC2 compliance requires audit logging")
        if self.security.session_timeout_minutes < 15:
            security_issues.append(
                "Session timeout too short for enterprise security")
        if security_issues:
            issues['security'] = security_issues

        # Validate deployment configuration
        deployment_issues = []
        if self.deployment.min_instances < 1:
            deployment_issues.append("Minimum instances must be at least 1")
        if self.deployment.min_instances > self.deployment.max_instances:
            deployment_issues.append(
                "Minimum instances cannot exceed maximum instances")
        if not self.deployment.backup_enabled and self.environment == "production":
            deployment_issues.append(
                "Backup should be enabled for production environment")
        if deployment_issues:
            issues['deployment'] = deployment_issues

        # Validate performance configuration
        performance_issues = []
        if self.performance.query_timeout_ms < 1000:
            performance_issues.append(
                "Query timeout too short for enterprise workloads")
        if self.performance.max_concurrent_queries < 10:
            performance_issues.append(
                "Max concurrent queries too low for enterprise scale")
        if performance_issues:
            issues['performance'] = performance_issues

        return issues

    def save_config(self, output_file: Optional[Union[str, Path]] = None) -> None:
        """Save current configuration to file."""
        if output_file is None:
            output_file = f"enterprise-{self.environment}.yaml"

        config_data = {
            'cluster': asdict(self.cluster),
            'security': asdict(self.security),
            'deployment': asdict(self.deployment),
            'performance': asdict(self.performance),
            'tenant': asdict(self.tenant)
        }

        output_path = Path(output_file)

        try:
            with open(output_path, 'w') as f:
                if output_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_data, f,
                              default_flow_style=False, indent=2)
                elif output_path.suffix.lower() == '.json':
                    json.dump(config_data, f, indent=2)
                else:
                    yaml.dump(config_data, f,
                              default_flow_style=False, indent=2)

            logger.info(f"Configuration saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving configuration to {output_path}: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'cluster': asdict(self.cluster),
            'security': asdict(self.security),
            'deployment': asdict(self.deployment),
            'performance': asdict(self.performance),
            'tenant': asdict(self.tenant)
        }

    def __str__(self) -> str:
        """String representation of configuration."""
        return f"EnterpriseConfig(environment={self.environment})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"EnterpriseConfig(environment='{self.environment}', "
            f"cluster_nodes={len(self.cluster.nodes)}, "
            f"security_enabled={self.security.rbac_enabled}, "
            f"cloud_provider='{self.deployment.cloud_provider}')"
        )


def load_enterprise_config(
    environment: str = "production",
    config_file: Optional[str] = None
) -> EnterpriseConfig:
    """
    Convenience function to load enterprise configuration.

    Args:
        environment: Target environment (dev, staging, production)
        config_file: Optional path to configuration file

    Returns:
        EnterpriseConfig instance
    """
    return EnterpriseConfig(environment=environment, config_file=config_file)


def create_sample_config(output_file: str = "enterprise-sample.yaml") -> None:
    """Create a sample enterprise configuration file."""
    config = EnterpriseConfig(environment="sample")
    config.save_config(output_file)

    print(f"Sample enterprise configuration created: {output_file}")
    print("Customize this file for your enterprise deployment.")

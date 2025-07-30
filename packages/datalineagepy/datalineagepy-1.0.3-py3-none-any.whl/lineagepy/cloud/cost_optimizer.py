"""
Cloud cost optimizer for analyzing and optimizing costs across multiple cloud providers.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..core.tracker import LineageTracker
from ..connectors.cloud_base import CloudStorageConnector

logger = logging.getLogger(__name__)


class CloudCostOptimizer:
    """
    Cloud cost optimizer for multi-cloud cost analysis and optimization.

    Features:
    - Cost analysis across cloud providers
    - Storage tier optimization recommendations
    - Data transfer cost analysis
    - Usage pattern analysis
    - Cost optimization recommendations
    """

    def __init__(self,
                 cloud_connectors: Dict[str, CloudStorageConnector],
                 tracker: LineageTracker):
        """
        Initialize cost optimizer.

        Args:
            cloud_connectors: Dict of cloud_name -> connector mappings
            tracker: LineageTracker instance for usage analysis
        """
        self.cloud_connectors = cloud_connectors
        self.tracker = tracker

        # Cost models (simplified placeholders)
        self.cost_models = {
            'aws': {
                's3_standard': 0.023,  # per GB/month
                's3_ia': 0.0125,
                's3_glacier': 0.004,
                'data_transfer_out': 0.09  # per GB
            },
            'gcp': {
                'gcs_standard': 0.020,
                'gcs_nearline': 0.010,
                'gcs_coldline': 0.004,
                'data_transfer_out': 0.08
            },
            'azure': {
                'blob_hot': 0.0184,
                'blob_cool': 0.01,
                'blob_archive': 0.00099,
                'data_transfer_out': 0.087
            }
        }

    def analyze_costs(self, time_period: str = "30d") -> Dict[str, Any]:
        """
        Analyze costs across all cloud providers.

        Args:
            time_period: Time period for analysis (e.g., "30d", "7d")

        Returns:
            Cost analysis results
        """
        analysis = {
            'time_period': time_period,
            'analyzed_at': datetime.now().isoformat(),
            'cloud_costs': {},
            'total_estimated_cost': 0.0,
            'cost_breakdown': {}
        }

        for cloud_name, connector in self.cloud_connectors.items():
            try:
                cloud_analysis = self._analyze_cloud_costs(
                    cloud_name, connector, time_period)
                analysis['cloud_costs'][cloud_name] = cloud_analysis
                analysis['total_estimated_cost'] += cloud_analysis.get(
                    'total_cost', 0.0)
            except Exception as e:
                logger.warning(
                    f"Failed to analyze costs for {cloud_name}: {str(e)}")
                analysis['cloud_costs'][cloud_name] = {'error': str(e)}

        # Generate cost breakdown
        analysis['cost_breakdown'] = self._generate_cost_breakdown(
            analysis['cloud_costs'])

        return analysis

    def optimize_costs(self, recommendations: bool = True) -> Dict[str, Any]:
        """
        Generate cost optimization recommendations.

        Args:
            recommendations: Whether to generate specific recommendations

        Returns:
            Optimization results and recommendations
        """
        optimization = {
            'analyzed_at': datetime.now().isoformat(),
            'potential_savings': 0.0,
            'recommendations': [],
            'cloud_optimizations': {}
        }

        for cloud_name, connector in self.cloud_connectors.items():
            try:
                cloud_optimization = self._optimize_cloud_costs(
                    cloud_name, connector)
                optimization['cloud_optimizations'][cloud_name] = cloud_optimization
                optimization['potential_savings'] += cloud_optimization.get(
                    'potential_savings', 0.0)

                if recommendations:
                    optimization['recommendations'].extend(
                        cloud_optimization.get('recommendations', [])
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to optimize costs for {cloud_name}: {str(e)}")
                optimization['cloud_optimizations'][cloud_name] = {
                    'error': str(e)}

        return optimization

    def get_usage_patterns(self) -> Dict[str, Any]:
        """Analyze usage patterns from lineage tracking."""
        patterns = {
            'analyzed_at': datetime.now().isoformat(),
            'total_operations': len(self.tracker.operations),
            'operation_types': {},
            'cloud_usage': {},
            'peak_usage_hours': [],
            'data_transfer_patterns': []
        }

        # Analyze operations
        for operation in self.tracker.operations:
            op_name = operation.get('operation_name', 'unknown')
            if op_name not in patterns['operation_types']:
                patterns['operation_types'][op_name] = 0
            patterns['operation_types'][op_name] += 1

            # Analyze cloud usage
            context = operation.get('context', {})
            cloud = context.get('cloud_provider')
            if cloud:
                if cloud not in patterns['cloud_usage']:
                    patterns['cloud_usage'][cloud] = 0
                patterns['cloud_usage'][cloud] += 1

        return patterns

    def _analyze_cloud_costs(self, cloud_name: str,
                             connector: CloudStorageConnector,
                             time_period: str) -> Dict[str, Any]:
        """Analyze costs for specific cloud provider."""
        analysis = {
            'cloud_name': cloud_name,
            'connector_type': type(connector).__name__,
            'storage_costs': 0.0,
            'transfer_costs': 0.0,
            'total_cost': 0.0,
            'object_count': 0,
            'total_size_gb': 0.0
        }

        try:
            # Get object list (limited sample for cost estimation)
            if hasattr(connector, 'list_objects'):
                objects = connector.list_objects(max_objects=1000)
                analysis['object_count'] = len(objects)

                # Calculate total size
                total_size_bytes = sum(obj.get('size', 0) for obj in objects)
                analysis['total_size_gb'] = total_size_bytes / (1024**3)

                # Estimate storage costs
                cost_model = self.cost_models.get(cloud_name.lower(), {})
                storage_rate = list(cost_model.values())[
                    0] if cost_model else 0.02  # Default rate
                analysis['storage_costs'] = analysis['total_size_gb'] * \
                    storage_rate

                # Estimate transfer costs (simplified)
                transfer_operations = self._count_transfer_operations(
                    cloud_name)
                transfer_rate = cost_model.get('data_transfer_out', 0.09)
                analysis['transfer_costs'] = transfer_operations * \
                    0.1 * transfer_rate  # Estimate

                analysis['total_cost'] = analysis['storage_costs'] + \
                    analysis['transfer_costs']

        except Exception as e:
            analysis['error'] = str(e)

        return analysis

    def _optimize_cloud_costs(self, cloud_name: str,
                              connector: CloudStorageConnector) -> Dict[str, Any]:
        """Generate optimization recommendations for specific cloud."""
        optimization = {
            'cloud_name': cloud_name,
            'potential_savings': 0.0,
            'recommendations': []
        }

        try:
            # Analyze object access patterns
            if hasattr(connector, 'list_objects'):
                objects = connector.list_objects(max_objects=500)

                # Find old objects for archival
                old_objects = []
                for obj in objects:
                    last_modified = obj.get('last_modified')
                    if last_modified:
                        # Convert to datetime if needed
                        if isinstance(last_modified, str):
                            from dateutil.parser import parse
                            last_modified = parse(last_modified)

                        age_days = (datetime.now(
                            last_modified.tzinfo) - last_modified).days
                        if age_days > 90:  # Objects older than 90 days
                            old_objects.append(obj)

                if old_objects:
                    # Calculate potential savings from archival
                    total_size_gb = sum(obj.get('size', 0)
                                        for obj in old_objects) / (1024**3)
                    current_rate = 0.023  # Standard storage rate
                    archive_rate = 0.004  # Archive storage rate
                    monthly_savings = total_size_gb * \
                        (current_rate - archive_rate)

                    # Annual savings
                    optimization['potential_savings'] += monthly_savings * 12
                    optimization['recommendations'].append({
                        'type': 'storage_tier_optimization',
                        'description': f'Archive {len(old_objects)} old objects to reduce costs',
                        'potential_annual_savings': monthly_savings * 12,
                        'objects_affected': len(old_objects),
                        'size_gb': total_size_gb
                    })

                # Find duplicate objects
                object_keys = [obj['key'] for obj in objects]
                duplicate_patterns = self._find_duplicate_patterns(object_keys)

                if duplicate_patterns:
                    optimization['recommendations'].append({
                        'type': 'duplicate_cleanup',
                        'description': f'Clean up {len(duplicate_patterns)} potential duplicate patterns',
                        'patterns_found': len(duplicate_patterns),
                        'action': 'Review and remove unnecessary duplicates'
                    })

        except Exception as e:
            optimization['error'] = str(e)

        return optimization

    def _generate_cost_breakdown(self, cloud_costs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cost breakdown across providers."""
        breakdown = {
            'by_provider': {},
            'by_cost_type': {
                'storage': 0.0,
                'transfer': 0.0
            },
            'largest_cost_driver': None
        }

        total_cost = 0.0
        for cloud_name, cost_data in cloud_costs.items():
            if 'error' not in cost_data:
                cloud_cost = cost_data.get('total_cost', 0.0)
                breakdown['by_provider'][cloud_name] = cloud_cost
                breakdown['by_cost_type']['storage'] += cost_data.get(
                    'storage_costs', 0.0)
                breakdown['by_cost_type']['transfer'] += cost_data.get(
                    'transfer_costs', 0.0)
                total_cost += cloud_cost

        # Find largest cost driver
        if breakdown['by_provider']:
            largest_provider = max(
                breakdown['by_provider'].items(), key=lambda x: x[1])
            breakdown['largest_cost_driver'] = {
                'provider': largest_provider[0],
                'cost': largest_provider[1],
                'percentage': (largest_provider[1] / total_cost * 100) if total_cost > 0 else 0
            }

        return breakdown

    def _count_transfer_operations(self, cloud_name: str) -> int:
        """Count data transfer operations for a cloud provider."""
        count = 0
        for operation in self.tracker.operations:
            context = operation.get('context', {})
            if context.get('cloud_provider') == cloud_name:
                op_name = operation.get('operation_name', '')
                if any(term in op_name.lower() for term in ['transfer', 'sync', 'copy', 'upload']):
                    count += 1
        return count

    def _find_duplicate_patterns(self, object_keys: List[str]) -> List[str]:
        """Find potential duplicate file patterns."""
        patterns = []

        # Simple pattern detection based on similar names
        key_groups = {}
        for key in object_keys:
            # Group by base name (without timestamps/versions)
            import re
            base_name = re.sub(r'[\d\-_\.]+$', '', key)
            if base_name not in key_groups:
                key_groups[base_name] = []
            key_groups[base_name].append(key)

        # Find groups with multiple files
        for base_name, keys in key_groups.items():
            if len(keys) > 1 and len(base_name) > 5:  # Meaningful base name
                patterns.append(base_name)

        return patterns

    def __str__(self) -> str:
        return f"CloudCostOptimizer(clouds={list(self.cloud_connectors.keys())})"

    def __repr__(self) -> str:
        return self.__str__()

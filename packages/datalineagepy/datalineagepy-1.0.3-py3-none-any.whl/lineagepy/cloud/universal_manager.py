"""
Universal Cloud Manager for orchestrating multi-cloud operations with lineage tracking.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import pandas as pd

from ..core.tracker import LineageTracker
from ..connectors.cloud_base import CloudStorageConnector
from .cross_cloud_pipeline import CrossCloudPipeline
from .cost_optimizer import CloudCostOptimizer

logger = logging.getLogger(__name__)


class UniversalCloudManager:
    """
    Universal manager for multi-cloud operations with comprehensive lineage tracking.

    Features:
    - Manage multiple cloud providers in a single interface
    - Cross-cloud data synchronization with lineage preservation
    - Cost optimization across cloud platforms
    - Universal data pipeline creation and execution
    - Cloud-agnostic data operations
    """

    def __init__(self,
                 cloud_connectors: Dict[str, CloudStorageConnector] = None,
                 tracker: LineageTracker = None,
                 default_cloud: str = None):
        """
        Initialize Universal Cloud Manager.

        Args:
            cloud_connectors: Dict of cloud_name -> connector mappings
            tracker: LineageTracker instance for tracking operations
            default_cloud: Default cloud provider for operations
        """
        self.cloud_connectors = cloud_connectors or {}
        self.tracker = tracker or LineageTracker()
        self.default_cloud = default_cloud

        # Ensure all connectors use the same tracker
        for connector in self.cloud_connectors.values():
            if hasattr(connector, 'tracker'):
                connector.tracker = self.tracker

        # Initialize components
        self.cost_optimizer = CloudCostOptimizer(
            self.cloud_connectors, self.tracker)

        # Connection status tracking
        self.connection_status = {}
        self._test_connections()

    def add_cloud_connector(self, cloud_name: str,
                            connector: CloudStorageConnector) -> None:
        """Add or update cloud connector."""
        connector.tracker = self.tracker
        self.cloud_connectors[cloud_name] = connector

        # Test connection
        try:
            connector.connect()
            self.connection_status[cloud_name] = True
            logger.info(f"Added cloud connector: {cloud_name}")
        except Exception as e:
            self.connection_status[cloud_name] = False
            logger.warning(f"Failed to connect to {cloud_name}: {str(e)}")

    def remove_cloud_connector(self, cloud_name: str) -> bool:
        """Remove cloud connector."""
        if cloud_name in self.cloud_connectors:
            connector = self.cloud_connectors.pop(cloud_name)
            self.connection_status.pop(cloud_name, None)

            # Disconnect if needed
            if hasattr(connector, 'disconnect'):
                connector.disconnect()

            logger.info(f"Removed cloud connector: {cloud_name}")
            return True
        return False

    def get_cloud_connector(self, cloud_name: str) -> CloudStorageConnector:
        """Get cloud connector by name."""
        if cloud_name not in self.cloud_connectors:
            raise ValueError(f"Cloud connector '{cloud_name}' not found")
        return self.cloud_connectors[cloud_name]

    def list_clouds(self) -> List[Dict[str, Any]]:
        """List all configured cloud providers."""
        clouds = []
        for cloud_name, connector in self.cloud_connectors.items():
            clouds.append({
                'name': cloud_name,
                'type': type(connector).__name__,
                'connected': self.connection_status.get(cloud_name, False),
                'info': self._get_connector_info(connector)
            })
        return clouds

    def create_pipeline(self) -> CrossCloudPipeline:
        """Create a new cross-cloud pipeline."""
        return CrossCloudPipeline(self.cloud_connectors, self.tracker)

    def sync_between_clouds(self,
                            source: str,
                            targets: List[str],
                            preserve_lineage: bool = True,
                            schedule: str = None,
                            filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Synchronize data between cloud providers.

        Args:
            source: Source specification in format 'cloud:path'
            targets: List of target specifications in format 'cloud:path'
            preserve_lineage: Whether to preserve lineage across sync
            schedule: Optional schedule for recurring sync
            filters: Optional filters for data selection

        Returns:
            Sync operation results
        """
        # Parse source
        source_cloud, source_path = self._parse_cloud_path(source)
        source_connector = self.get_cloud_connector(source_cloud)

        # Parse targets
        target_specs = []
        for target in targets:
            target_cloud, target_path = self._parse_cloud_path(target)
            target_connector = self.get_cloud_connector(target_cloud)
            target_specs.append((target_cloud, target_path, target_connector))

        sync_results = {
            'source': source,
            'targets': targets,
            'started_at': datetime.now().isoformat(),
            'operations': []
        }

        try:
            # List objects in source
            objects = source_connector.list_objects(prefix=source_path)

            # Apply filters if specified
            if filters:
                objects = self._apply_filters(objects, filters)

            # Sync to each target
            for target_cloud, target_path, target_connector in target_specs:
                target_operations = []

                for obj in objects:
                    try:
                        # Download from source
                        local_path = source_connector.download_object(
                            obj['key'])

                        # Upload to target
                        target_key = self._compute_target_key(
                            obj['key'], source_path, target_path)
                        success = target_connector.upload_object(
                            local_path, target_key, obj)

                        if success and preserve_lineage:
                            self._track_cross_cloud_sync(
                                source_cloud, obj['key'],
                                target_cloud, target_key
                            )

                        target_operations.append({
                            'source_key': obj['key'],
                            'target_key': target_key,
                            'success': success,
                            'size': obj.get('size', 0)
                        })

                        # Clean up temp file
                        import os
                        if os.path.exists(local_path):
                            os.unlink(local_path)

                    except Exception as e:
                        logger.error(
                            f"Failed to sync {obj['key']} to {target_cloud}: {str(e)}")
                        target_operations.append({
                            'source_key': obj['key'],
                            'target_key': None,
                            'success': False,
                            'error': str(e)
                        })

                sync_results['operations'].append({
                    'target': f"{target_cloud}:{target_path}",
                    'operations': target_operations,
                    'success_count': sum(1 for op in target_operations if op['success']),
                    'total_count': len(target_operations)
                })

            sync_results['completed_at'] = datetime.now().isoformat()
            sync_results['overall_success'] = all(
                op['success_count'] == op['total_count']
                for op in sync_results['operations']
            )

            logger.info(
                f"Completed cross-cloud sync from {source} to {len(targets)} targets")
            return sync_results

        except Exception as e:
            sync_results['error'] = str(e)
            sync_results['completed_at'] = datetime.now().isoformat()
            logger.error(f"Cross-cloud sync failed: {str(e)}")
            raise

    def read_from_cloud(self, cloud_path: str, **kwargs) -> pd.DataFrame:
        """
        Read data from any cloud provider.

        Args:
            cloud_path: Path in format 'cloud:path'
            **kwargs: Additional read options

        Returns:
            DataFrame with data
        """
        cloud_name, object_key = self._parse_cloud_path(cloud_path)
        connector = self.get_cloud_connector(cloud_name)

        # Determine file format and read accordingly
        if object_key.endswith('.parquet'):
            return connector.read_parquet(object_key, **kwargs)
        elif object_key.endswith('.csv'):
            return connector.read_csv(object_key, **kwargs)
        elif object_key.endswith('.json'):
            return connector.read_json(object_key, **kwargs)
        else:
            raise ValueError(f"Unsupported file format for {object_key}")

    def write_to_cloud(self, df: pd.DataFrame, cloud_path: str, **kwargs) -> bool:
        """
        Write DataFrame to any cloud provider.

        Args:
            df: DataFrame to write
            cloud_path: Path in format 'cloud:path'
            **kwargs: Additional write options

        Returns:
            True if successful
        """
        cloud_name, object_key = self._parse_cloud_path(cloud_path)
        connector = self.get_cloud_connector(cloud_name)

        # Determine file format and write accordingly
        if object_key.endswith('.parquet'):
            return connector.write_parquet(df, object_key, **kwargs)
        elif object_key.endswith('.csv'):
            return connector.write_csv(df, object_key, **kwargs)
        elif object_key.endswith('.json'):
            return connector.write_json(df, object_key, **kwargs)
        else:
            raise ValueError(f"Unsupported file format for {object_key}")

    def get_cost_analysis(self, time_period: str = "30d") -> Dict[str, Any]:
        """Get cost analysis across all cloud providers."""
        return self.cost_optimizer.analyze_costs(time_period)

    def optimize_costs(self, recommendations: bool = True) -> Dict[str, Any]:
        """Get cost optimization recommendations."""
        return self.cost_optimizer.optimize_costs(recommendations)

    def get_lineage_summary(self) -> Dict[str, Any]:
        """Get comprehensive lineage summary across all clouds."""
        summary = self.tracker.get_lineage_summary()

        # Add cloud-specific information
        cloud_summary = {
            'clouds_configured': len(self.cloud_connectors),
            'clouds_connected': sum(1 for status in self.connection_status.values() if status),
            'cloud_operations': {},
            'cross_cloud_transfers': 0
        }

        # Count operations by cloud
        for operation in self.tracker.operations:
            operation_context = operation.get('context', {})
            if 'cloud_provider' in operation_context:
                cloud = operation_context['cloud_provider']
                if cloud not in cloud_summary['cloud_operations']:
                    cloud_summary['cloud_operations'][cloud] = 0
                cloud_summary['cloud_operations'][cloud] += 1

            # Count cross-cloud operations
            if 'cross_cloud' in operation.get('operation_name', ''):
                cloud_summary['cross_cloud_transfers'] += 1

        summary.update(cloud_summary)
        return summary

    def _test_connections(self) -> None:
        """Test all cloud connections."""
        for cloud_name, connector in self.cloud_connectors.items():
            try:
                if hasattr(connector, 'test_connection'):
                    connected = connector.test_connection()
                else:
                    connector.connect()
                    connected = True
                self.connection_status[cloud_name] = connected
            except Exception as e:
                self.connection_status[cloud_name] = False
                logger.warning(
                    f"Connection test failed for {cloud_name}: {str(e)}")

    def _parse_cloud_path(self, cloud_path: str) -> tuple:
        """Parse cloud path into provider and object key."""
        if ':' not in cloud_path:
            if self.default_cloud:
                return self.default_cloud, cloud_path
            else:
                raise ValueError(
                    "No cloud provider specified and no default cloud set")

        parts = cloud_path.split(':', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid cloud path format: {cloud_path}")

        return parts[0], parts[1]

    def _get_connector_info(self, connector: CloudStorageConnector) -> Dict[str, Any]:
        """Get connector information."""
        try:
            if hasattr(connector, 'get_connection_info'):
                return connector.get_connection_info()
            else:
                return {
                    'type': type(connector).__name__,
                    'bucket_name': getattr(connector, 'bucket_name', None),
                    'region': getattr(connector, 'region', None)
                }
        except Exception:
            return {'type': type(connector).__name__}

    def _apply_filters(self, objects: List[Dict[str, Any]],
                       filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to object list."""
        filtered_objects = objects

        # Size filter
        if 'min_size' in filters:
            filtered_objects = [obj for obj in filtered_objects
                                if obj.get('size', 0) >= filters['min_size']]

        if 'max_size' in filters:
            filtered_objects = [obj for obj in filtered_objects
                                if obj.get('size', 0) <= filters['max_size']]

        # Date filter
        if 'after_date' in filters:
            after_date = pd.to_datetime(filters['after_date'])
            filtered_objects = [obj for obj in filtered_objects
                                if pd.to_datetime(obj.get('last_modified')) >= after_date]

        # Pattern filter
        if 'pattern' in filters:
            import re
            pattern = re.compile(filters['pattern'])
            filtered_objects = [obj for obj in filtered_objects
                                if pattern.search(obj['key'])]

        return filtered_objects

    def _compute_target_key(self, source_key: str, source_prefix: str,
                            target_prefix: str) -> str:
        """Compute target key from source key and prefixes."""
        if source_key.startswith(source_prefix):
            relative_key = source_key[len(source_prefix):]
            return target_prefix + relative_key
        else:
            return target_prefix + source_key

    def _track_cross_cloud_sync(self, source_cloud: str, source_key: str,
                                target_cloud: str, target_key: str) -> None:
        """Track cross-cloud synchronization in lineage."""
        if self.tracker:
            from ..core.nodes import CloudNode

            # Create source node
            source_node = CloudNode(
                node_id=f"{source_cloud}_{hash(source_key)}",
                name=f"{source_cloud}: {source_key}",
                bucket_name=source_cloud,
                object_key=source_key,
                cloud_provider=source_cloud
            )

            # Create target node
            target_node = CloudNode(
                node_id=f"{target_cloud}_{hash(target_key)}",
                name=f"{target_cloud}: {target_key}",
                bucket_name=target_cloud,
                object_key=target_key,
                cloud_provider=target_cloud
            )

            # Add nodes and edge
            self.tracker.add_node(source_node)
            self.tracker.add_node(target_node)
            self.tracker.add_edge(source_node.node_id, target_node.node_id,
                                  "cross_cloud_sync")

            # Add operation context
            self.tracker.add_operation_context(
                operation_name="cross_cloud_sync",
                context={
                    'source_cloud': source_cloud,
                    'source_key': source_key,
                    'target_cloud': target_cloud,
                    'target_key': target_key,
                    'timestamp': datetime.now().isoformat()
                }
            )

    def __str__(self) -> str:
        return f"UniversalCloudManager(clouds={list(self.cloud_connectors.keys())})"

    def __repr__(self) -> str:
        return self.__str__()

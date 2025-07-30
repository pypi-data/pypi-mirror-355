"""
Universal Stream Manager for multi-platform streaming lineage orchestration.

This module provides comprehensive multi-platform streaming management including:
- Cross-platform streaming lineage tracking
- Universal stream catalog and metadata management
- Stream migration tracking and platform abstraction
- Cost optimization across streaming platforms
- Unified monitoring and alerting
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import json
import time

from ..core.tracker import LineageTracker
from .streaming_base import StreamingConnector

logger = logging.getLogger(__name__)


class CrossPlatformStreamPipeline:
    """
    Cross-platform streaming pipeline for data flow orchestration.

    Enables data movement and transformation across multiple streaming platforms
    with comprehensive lineage tracking.
    """

    def __init__(self,
                 stream_manager: 'UniversalStreamManager',
                 pipeline_id: str = None):
        """
        Initialize cross-platform stream pipeline.

        Args:
            stream_manager: Universal stream manager instance
            pipeline_id: Unique pipeline identifier
        """
        self.stream_manager = stream_manager
        self.pipeline_id = pipeline_id or f"pipeline_{int(time.time())}"

        # Pipeline stages
        self.stages = []
        self.current_stage = 0

        # Execution state
        self.executed = False
        self.execution_results = {}
        self.execution_start_time = None
        self.execution_end_time = None

    def source(self, platform: str, stream_identifier: str, **kwargs):
        """
        Add source stage to pipeline.

        Args:
            platform: Source streaming platform
            stream_identifier: Stream/topic identifier
            **kwargs: Additional source configuration
        """
        stage = {
            'type': 'source',
            'platform': platform,
            'stream_identifier': stream_identifier,
            'config': kwargs,
            'stage_id': len(self.stages)
        }
        self.stages.append(stage)
        logger.debug(f"Added source stage: {platform}:{stream_identifier}")
        return self

    def transform(self, platform: str, processor_config: Dict[str, Any], **kwargs):
        """
        Add transformation stage to pipeline.

        Args:
            platform: Processing platform
            processor_config: Processor configuration
            **kwargs: Additional transform configuration
        """
        stage = {
            'type': 'transform',
            'platform': platform,
            'processor_config': processor_config,
            'config': kwargs,
            'stage_id': len(self.stages)
        }
        self.stages.append(stage)
        logger.debug(f"Added transform stage: {platform}")
        return self

    def sink(self, platform: str, stream_identifier: str, **kwargs):
        """
        Add sink stage to pipeline.

        Args:
            platform: Target streaming platform
            stream_identifier: Target stream/topic identifier
            **kwargs: Additional sink configuration
        """
        stage = {
            'type': 'sink',
            'platform': platform,
            'stream_identifier': stream_identifier,
            'config': kwargs,
            'stage_id': len(self.stages)
        }
        self.stages.append(stage)
        logger.debug(f"Added sink stage: {platform}:{stream_identifier}")
        return self

    def execute(self) -> Dict[str, Any]:
        """
        Execute the cross-platform streaming pipeline.

        Returns:
            Pipeline execution results
        """
        if self.executed:
            logger.warning(f"Pipeline {self.pipeline_id} already executed")
            return self.execution_results

        self.execution_start_time = datetime.now()
        logger.info(f"Executing cross-platform pipeline: {self.pipeline_id}")

        try:
            # Execute each stage
            for stage in self.stages:
                stage_result = self._execute_stage(stage)
                self.execution_results[f"stage_{stage['stage_id']}"] = stage_result

            # Track pipeline lineage
            self._track_pipeline_lineage()

            self.executed = True
            self.execution_end_time = datetime.now()

            logger.info(f"Pipeline {self.pipeline_id} executed successfully")

        except Exception as e:
            logger.error(f"Pipeline {self.pipeline_id} execution failed: {e}")
            self.execution_results['error'] = str(e)
            raise

        return self.execution_results

    def _execute_stage(self, stage: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual pipeline stage."""
        platform = stage['platform']
        stage_type = stage['type']

        logger.debug(f"Executing {stage_type} stage on {platform}")

        if platform not in self.stream_manager.stream_connectors:
            raise ValueError(f"Platform {platform} not configured")

        connector = self.stream_manager.stream_connectors[platform]

        if stage_type == 'source':
            return self._execute_source_stage(stage, connector)
        elif stage_type == 'transform':
            return self._execute_transform_stage(stage, connector)
        elif stage_type == 'sink':
            return self._execute_sink_stage(stage, connector)
        else:
            raise ValueError(f"Unknown stage type: {stage_type}")

    def _execute_source_stage(self, stage: Dict[str, Any], connector: StreamingConnector) -> Dict[str, Any]:
        """Execute source stage."""
        stream_identifier = stage['stream_identifier']

        # Track source in lineage
        source_node_id = connector.track_topic(stream_identifier)

        return {
            'stage_type': 'source',
            'platform': stage['platform'],
            'stream_identifier': stream_identifier,
            'node_id': source_node_id,
            'success': True,
            'timestamp': datetime.now().isoformat()
        }

    def _execute_transform_stage(self, stage: Dict[str, Any], connector: StreamingConnector) -> Dict[str, Any]:
        """Execute transformation stage."""
        processor_config = stage['processor_config']

        # Create processor node
        processor_node_id = f"{stage['platform']}_processor_{self.pipeline_id}_{stage['stage_id']}"
        connector.create_stream_node(
            node_id=processor_node_id,
            stream_type="processor",
            processor_config=processor_config
        )

        return {
            'stage_type': 'transform',
            'platform': stage['platform'],
            'processor_config': processor_config,
            'node_id': processor_node_id,
            'success': True,
            'timestamp': datetime.now().isoformat()
        }

    def _execute_sink_stage(self, stage: Dict[str, Any], connector: StreamingConnector) -> Dict[str, Any]:
        """Execute sink stage."""
        stream_identifier = stage['stream_identifier']

        # Track sink in lineage
        sink_node_id = connector.track_topic(stream_identifier)

        return {
            'stage_type': 'sink',
            'platform': stage['platform'],
            'stream_identifier': stream_identifier,
            'node_id': sink_node_id,
            'success': True,
            'timestamp': datetime.now().isoformat()
        }

    def _track_pipeline_lineage(self):
        """Track lineage connections between pipeline stages."""
        for i in range(len(self.stages) - 1):
            current_stage = self.stages[i]
            next_stage = self.stages[i + 1]

            current_result = self.execution_results[f"stage_{current_stage['stage_id']}"]
            next_result = self.execution_results[f"stage_{next_stage['stage_id']}"]

            if 'node_id' in current_result and 'node_id' in next_result:
                # Add edge between stages
                current_connector = self.stream_manager.stream_connectors[current_stage['platform']]
                current_connector.add_stream_edge(
                    source_node_id=current_result['node_id'],
                    target_node_id=next_result['node_id'],
                    operation="pipeline_flow",
                    metadata={
                        'pipeline_id': self.pipeline_id,
                        'stage_transition': f"{current_stage['type']}_to_{next_stage['type']}"
                    }
                )

    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get pipeline execution summary."""
        duration = None
        if self.execution_start_time and self.execution_end_time:
            duration = (self.execution_end_time -
                        self.execution_start_time).total_seconds()

        return {
            'pipeline_id': self.pipeline_id,
            'stage_count': len(self.stages),
            'executed': self.executed,
            'execution_duration': duration,
            'platforms_used': list(set(stage['platform'] for stage in self.stages)),
            'stage_summary': [
                {
                    'stage_id': stage['stage_id'],
                    'type': stage['type'],
                    'platform': stage['platform']
                }
                for stage in self.stages
            ]
        }


class UniversalStreamManager:
    """
    Universal manager for multi-platform streaming operations with lineage tracking.

    Features:
    - Manage multiple streaming platforms in a unified interface
    - Cross-platform stream catalog and metadata management
    - Stream migration tracking and platform abstraction
    - Cost optimization across streaming platforms
    - Universal monitoring and alerting
    """

    def __init__(self,
                 stream_connectors: Dict[str, StreamingConnector] = None,
                 tracker: LineageTracker = None,
                 default_platform: str = None):
        """
        Initialize Universal Stream Manager.

        Args:
            stream_connectors: Dict of platform_name -> connector mappings
            tracker: LineageTracker instance for tracking operations
            default_platform: Default streaming platform for operations
        """
        self.stream_connectors = stream_connectors or {}
        self.tracker = tracker or LineageTracker()
        self.default_platform = default_platform

        # Ensure all connectors use the same tracker
        for connector in self.stream_connectors.values():
            if hasattr(connector, 'tracker'):
                connector.tracker = self.tracker

        # Stream catalog
        self.stream_catalog = {}
        self._refresh_stream_catalog()

        # Platform statistics
        self.platform_stats = {}
        self._initialize_platform_stats()

        # Migration tracking
        self.migration_history = []

    def add_stream_connector(self, platform_name: str, connector: StreamingConnector):
        """
        Add streaming platform connector.

        Args:
            platform_name: Name of the streaming platform
            connector: StreamingConnector instance
        """
        connector.tracker = self.tracker
        self.stream_connectors[platform_name] = connector

        # Refresh catalog
        self._refresh_platform_catalog(platform_name)

        logger.info(f"Added streaming platform: {platform_name}")

    def remove_stream_connector(self, platform_name: str) -> bool:
        """
        Remove streaming platform connector.

        Args:
            platform_name: Name of the platform to remove

        Returns:
            True if removed successfully
        """
        if platform_name in self.stream_connectors:
            connector = self.stream_connectors.pop(platform_name)

            # Disconnect if needed
            if hasattr(connector, 'disconnect'):
                connector.disconnect()

            # Remove from catalog
            self.stream_catalog.pop(platform_name, None)
            self.platform_stats.pop(platform_name, None)

            logger.info(f"Removed streaming platform: {platform_name}")
            return True
        return False

    def list_platforms(self) -> List[Dict[str, Any]]:
        """List all configured streaming platforms."""
        platforms = []
        for platform_name, connector in self.stream_connectors.items():
            platform_info = {
                'name': platform_name,
                'type': type(connector).__name__,
                'connected': getattr(connector, 'connected', False),
                'stream_count': len(self.stream_catalog.get(platform_name, {})),
                'stats': self.platform_stats.get(platform_name, {})
            }
            platforms.append(platform_info)
        return platforms

    def create_cross_platform_pipeline(self) -> CrossPlatformStreamPipeline:
        """Create a new cross-platform streaming pipeline."""
        return CrossPlatformStreamPipeline(self)

    def sync_stream_across_platforms(self,
                                     source_platform: str,
                                     source_stream: str,
                                     target_platform: str,
                                     target_stream: str,
                                     sync_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Synchronize stream data across platforms.

        Args:
            source_platform: Source streaming platform
            source_stream: Source stream identifier
            target_platform: Target streaming platform
            target_stream: Target stream identifier
            sync_config: Synchronization configuration

        Returns:
            Sync operation results
        """
        if source_platform not in self.stream_connectors:
            raise ValueError(
                f"Source platform {source_platform} not configured")
        if target_platform not in self.stream_connectors:
            raise ValueError(
                f"Target platform {target_platform} not configured")

        sync_results = {
            'sync_id': f"sync_{int(time.time())}",
            'source': f"{source_platform}:{source_stream}",
            'target': f"{target_platform}:{target_stream}",
            'started_at': datetime.now().isoformat(),
            'config': sync_config or {}
        }

        try:
            source_connector = self.stream_connectors[source_platform]
            target_connector = self.stream_connectors[target_platform]

            # Get source stream metadata
            source_metadata = source_connector.get_topic_metadata(
                source_stream)

            # Create target stream if needed
            target_metadata = target_connector.get_topic_metadata(
                target_stream)
            if not target_metadata:
                target_connector.track_topic(target_stream)

            # Track cross-platform lineage
            source_node_id = source_connector.track_topic(source_stream)
            target_node_id = target_connector.track_topic(target_stream)

            # Add cross-platform edge
            self.tracker.add_edge(
                source_node_id,
                target_node_id,
                {
                    'operation': 'cross_platform_sync',
                    'sync_id': sync_results['sync_id'],
                    'source_platform': source_platform,
                    'target_platform': target_platform,
                    'timestamp': datetime.now().isoformat()
                }
            )

            sync_results.update({
                'success': True,
                'source_node_id': source_node_id,
                'target_node_id': target_node_id,
                'completed_at': datetime.now().isoformat()
            })

            logger.info(
                f"Stream sync completed: {source_platform}:{source_stream} -> {target_platform}:{target_stream}")

        except Exception as e:
            sync_results.update({
                'success': False,
                'error': str(e),
                'failed_at': datetime.now().isoformat()
            })
            logger.error(f"Stream sync failed: {e}")

        return sync_results

    def monitor_cross_platform_flow(self,
                                    source_platform: str,
                                    target_platform: str,
                                    data_category: str = None) -> Dict[str, Any]:
        """
        Monitor data flow between platforms.

        Args:
            source_platform: Source platform to monitor
            target_platform: Target platform to monitor
            data_category: Optional data category filter

        Returns:
            Cross-platform flow monitoring data
        """
        flow_metrics = {
            'source_platform': source_platform,
            'target_platform': target_platform,
            'data_category': data_category,
            'monitored_at': datetime.now().isoformat(),
            'flow_analysis': {}
        }

        try:
            # Get lineage edges between platforms
            cross_platform_edges = []
            for edge in self.tracker.get_all_edges():
                edge_metadata = edge.get('metadata', {})
                if (edge_metadata.get('source_platform') == source_platform and
                        edge_metadata.get('target_platform') == target_platform):
                    cross_platform_edges.append(edge)

            flow_metrics['flow_analysis'] = {
                'cross_platform_connections': len(cross_platform_edges),
                'active_syncs': len([e for e in cross_platform_edges if 'sync_id' in e.get('metadata', {})]),
                'last_flow_time': max([e.get('metadata', {}).get('timestamp', '') for e in cross_platform_edges], default=''),
                'flow_types': list(set([e.get('metadata', {}).get('operation') for e in cross_platform_edges]))
            }

            logger.debug(
                f"Monitored cross-platform flow: {source_platform} -> {target_platform}")

        except Exception as e:
            flow_metrics['error'] = str(e)
            logger.error(f"Failed to monitor cross-platform flow: {e}")

        return flow_metrics

    def get_universal_stream_catalog(self) -> Dict[str, Any]:
        """Get comprehensive stream catalog across all platforms."""
        catalog = {
            'platforms': list(self.stream_connectors.keys()),
            'total_streams': sum(len(streams) for streams in self.stream_catalog.values()),
            'last_updated': datetime.now().isoformat(),
            'platform_catalogs': {}
        }

        for platform_name, streams in self.stream_catalog.items():
            catalog['platform_catalogs'][platform_name] = {
                'stream_count': len(streams),
                'streams': streams
            }

        return catalog

    def optimize_cross_platform_costs(self) -> Dict[str, Any]:
        """Analyze and optimize costs across streaming platforms."""
        cost_analysis = {
            'analysis_timestamp': datetime.now().isoformat(),
            'platforms_analyzed': list(self.stream_connectors.keys()),
            'cost_optimization_recommendations': [],
            'potential_savings': {}
        }

        # Analyze each platform
        for platform_name in self.stream_connectors.keys():
            platform_recommendations = self._analyze_platform_costs(
                platform_name)
            cost_analysis['cost_optimization_recommendations'].extend(
                platform_recommendations)

        # Cross-platform optimization opportunities
        cross_platform_recommendations = self._analyze_cross_platform_optimization()
        cost_analysis['cost_optimization_recommendations'].extend(
            cross_platform_recommendations)

        logger.info("Completed cross-platform cost optimization analysis")
        return cost_analysis

    def _refresh_stream_catalog(self):
        """Refresh the universal stream catalog."""
        for platform_name in self.stream_connectors.keys():
            self._refresh_platform_catalog(platform_name)

    def _refresh_platform_catalog(self, platform_name: str):
        """Refresh catalog for specific platform."""
        try:
            connector = self.stream_connectors[platform_name]
            if hasattr(connector, 'list_topics'):
                topics = connector.list_topics()
                self.stream_catalog[platform_name] = {
                    topic['name']: topic for topic in topics
                }
            else:
                self.stream_catalog[platform_name] = {}
        except Exception as e:
            logger.warning(
                f"Failed to refresh catalog for {platform_name}: {e}")
            self.stream_catalog[platform_name] = {}

    def _initialize_platform_stats(self):
        """Initialize platform statistics."""
        for platform_name in self.stream_connectors.keys():
            self.platform_stats[platform_name] = {
                'streams_tracked': 0,
                'producers_tracked': 0,
                'consumers_tracked': 0,
                'last_activity': None
            }

    def _analyze_platform_costs(self, platform_name: str) -> List[Dict[str, Any]]:
        """Analyze costs for a specific platform."""
        recommendations = []

        # Example cost analysis logic
        stream_count = len(self.stream_catalog.get(platform_name, {}))

        if stream_count > 100:
            recommendations.append({
                'platform': platform_name,
                'type': 'stream_consolidation',
                'description': f"Consider consolidating {stream_count} streams to reduce costs",
                'potential_savings': '15-25%',
                'effort': 'medium'
            })

        return recommendations

    def _analyze_cross_platform_optimization(self) -> List[Dict[str, Any]]:
        """Analyze cross-platform optimization opportunities."""
        recommendations = []

        # Example cross-platform optimization
        platform_count = len(self.stream_connectors)

        if platform_count > 2:
            recommendations.append({
                'type': 'platform_consolidation',
                'description': f"Consider consolidating {platform_count} platforms to reduce operational overhead",
                'potential_savings': '20-30%',
                'effort': 'high'
            })

        return recommendations

    def get_universal_lineage_summary(self) -> Dict[str, Any]:
        """Get comprehensive lineage summary across all platforms."""
        return {
            'platforms': len(self.stream_connectors),
            'total_streams': sum(len(streams) for streams in self.stream_catalog.values()),
            'cross_platform_connections': len([
                edge for edge in self.tracker.get_all_edges()
                if 'cross_platform' in edge.get('metadata', {}).get('operation', '')
            ]),
            'lineage_nodes': len(self.tracker.get_all_nodes()),
            'lineage_edges': len(self.tracker.get_all_edges()),
            'last_updated': datetime.now().isoformat()
        }

    def __str__(self) -> str:
        """String representation."""
        return f"UniversalStreamManager(platforms={len(self.stream_connectors)})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"UniversalStreamManager(platforms={list(self.stream_connectors.keys())}, "
                f"streams={sum(len(s) for s in self.stream_catalog.values())})")

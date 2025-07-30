"""
Base classes for streaming data lineage tracking.

This module provides the foundational abstractions for all streaming platforms,
including the StreamingConnector base class and StreamNode representation.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable
import json

from ..core.tracker import LineageTracker
from ..core.nodes import BaseNode

logger = logging.getLogger(__name__)


class StreamNode(BaseNode):
    """
    Node representing streaming data sources/sinks.

    Extends BaseNode with streaming-specific metadata like throughput,
    schema registry information, and partition details.
    """

    def __init__(self,
                 node_id: str,
                 stream_type: str,
                 platform: str,
                 topic_name: str = None,
                 partition_count: int = None,
                 schema_id: str = None,
                 **kwargs):
        """
        Initialize stream node.

        Args:
            node_id: Unique identifier for the stream node
            stream_type: Type of stream (topic, partition, consumer_group, etc.)
            platform: Streaming platform (kafka, pulsar, kinesis)
            topic_name: Name of the topic/stream
            partition_count: Number of partitions
            schema_id: Schema registry ID for the stream
            **kwargs: Additional stream-specific metadata
        """
        super().__init__(node_id, node_type=f"stream_{stream_type}", **kwargs)

        self.stream_type = stream_type
        self.platform = platform
        self.topic_name = topic_name
        self.partition_count = partition_count
        self.schema_id = schema_id

        # Streaming-specific metadata
        self.throughput_metrics = kwargs.get('throughput_metrics', {})
        self.consumer_groups = kwargs.get('consumer_groups', [])
        self.retention_policy = kwargs.get('retention_policy', {})
        self.replication_factor = kwargs.get('replication_factor', 1)

    def update_throughput(self, messages_per_sec: float, bytes_per_sec: float):
        """Update throughput metrics for the stream."""
        self.throughput_metrics.update({
            'messages_per_sec': messages_per_sec,
            'bytes_per_sec': bytes_per_sec,
            'last_updated': datetime.now().isoformat()
        })
        logger.debug(
            f"Updated throughput for {self.node_id}: {messages_per_sec} msg/s")

    def add_consumer_group(self, group_id: str, offset_info: Dict[str, Any] = None):
        """Add consumer group information to the stream node."""
        consumer_info = {
            'group_id': group_id,
            'offset_info': offset_info or {},
            'registered_at': datetime.now().isoformat()
        }
        self.consumer_groups.append(consumer_info)
        logger.debug(f"Added consumer group {group_id} to {self.node_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert stream node to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'stream_type': self.stream_type,
            'platform': self.platform,
            'topic_name': self.topic_name,
            'partition_count': self.partition_count,
            'schema_id': self.schema_id,
            'throughput_metrics': self.throughput_metrics,
            'consumer_groups': self.consumer_groups,
            'retention_policy': self.retention_policy,
            'replication_factor': self.replication_factor
        })
        return base_dict


class StreamingConnector(ABC):
    """
    Abstract base class for streaming platform connectors.

    Provides the common interface and functionality that all streaming
    platform implementations must support.
    """

    def __init__(self,
                 platform_name: str,
                 connection_config: Dict[str, Any],
                 tracker: LineageTracker = None,
                 **kwargs):
        """
        Initialize streaming connector.

        Args:
            platform_name: Name of the streaming platform
            connection_config: Platform-specific connection configuration
            tracker: LineageTracker instance for lineage tracking
            **kwargs: Additional connector options
        """
        self.platform_name = platform_name
        self.connection_config = connection_config
        self.tracker = tracker or LineageTracker()

        # Connection state
        self.connected = False
        self.client = None

        # Streaming-specific configuration
        self.auto_track_lineage = kwargs.get('auto_track_lineage', True)
        self.track_schema_evolution = kwargs.get(
            'track_schema_evolution', True)
        self.batch_size = kwargs.get('batch_size', 1000)

        # Event handlers
        self._event_handlers = {
            'message_produced': [],
            'message_consumed': [],
            'schema_evolved': [],
            'partition_rebalanced': []
        }

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to streaming platform.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to streaming platform.

        Returns:
            True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def list_topics(self) -> List[Dict[str, Any]]:
        """
        List all available topics/streams.

        Returns:
            List of topic information dictionaries
        """
        pass

    @abstractmethod
    def get_topic_metadata(self, topic_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific topic.

        Args:
            topic_name: Name of the topic

        Returns:
            Topic metadata dictionary
        """
        pass

    @abstractmethod
    def track_producer(self,
                       topic_name: str,
                       source_identifier: str = None,
                       metadata: Dict[str, Any] = None) -> str:
        """
        Track producer lineage for a topic.

        Args:
            topic_name: Target topic name
            source_identifier: Source data identifier
            metadata: Additional producer metadata

        Returns:
            Producer lineage node ID
        """
        pass

    @abstractmethod
    def track_consumer(self,
                       topic_name: str,
                       consumer_group: str,
                       target_identifier: str = None,
                       metadata: Dict[str, Any] = None) -> str:
        """
        Track consumer lineage for a topic.

        Args:
            topic_name: Source topic name
            consumer_group: Consumer group ID
            target_identifier: Target data identifier
            metadata: Additional consumer metadata

        Returns:
            Consumer lineage node ID
        """
        pass

    def register_event_handler(self, event_type: str, handler: Callable):
        """
        Register event handler for streaming events.

        Args:
            event_type: Type of event (message_produced, message_consumed, etc.)
            handler: Event handler function
        """
        if event_type in self._event_handlers:
            self._event_handlers[event_type].append(handler)
            logger.debug(
                f"Registered {event_type} handler for {self.platform_name}")
        else:
            logger.warning(f"Unknown event type: {event_type}")

    def emit_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Emit streaming event to registered handlers.

        Args:
            event_type: Type of event
            event_data: Event data dictionary
        """
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    handler(event_data)
                except Exception as e:
                    logger.error(f"Error in {event_type} handler: {e}")

    def create_stream_node(self,
                           node_id: str,
                           stream_type: str,
                           topic_name: str = None,
                           **kwargs) -> StreamNode:
        """
        Create a new stream node and add to lineage tracker.

        Args:
            node_id: Unique node identifier
            stream_type: Type of stream node
            topic_name: Topic/stream name
            **kwargs: Additional node metadata

        Returns:
            Created StreamNode instance
        """
        node = StreamNode(
            node_id=node_id,
            stream_type=stream_type,
            platform=self.platform_name,
            topic_name=topic_name,
            **kwargs
        )

        if self.auto_track_lineage:
            self.tracker.add_node(node)
            logger.debug(f"Created stream node: {node_id}")

        return node

    def add_stream_edge(self,
                        source_node_id: str,
                        target_node_id: str,
                        operation: str,
                        metadata: Dict[str, Any] = None):
        """
        Add edge between stream nodes.

        Args:
            source_node_id: Source node ID
            target_node_id: Target node ID
            operation: Stream operation type
            metadata: Additional edge metadata
        """
        if self.auto_track_lineage:
            edge_metadata = {
                'operation': operation,
                'platform': self.platform_name,
                'timestamp': datetime.now().isoformat()
            }
            if metadata:
                edge_metadata.update(metadata)

            self.tracker.add_edge(
                source_node_id, target_node_id, edge_metadata)
            logger.debug(
                f"Added stream edge: {source_node_id} -> {target_node_id}")

    def track_schema_evolution(self,
                               topic_name: str,
                               old_schema: Dict[str, Any],
                               new_schema: Dict[str, Any],
                               compatibility_type: str = "unknown"):
        """
        Track schema evolution events.

        Args:
            topic_name: Topic with schema evolution
            old_schema: Previous schema definition
            new_schema: New schema definition
            compatibility_type: Type of compatibility (forward, backward, full)
        """
        if self.track_schema_evolution:
            evolution_event = {
                'topic_name': topic_name,
                'old_schema': old_schema,
                'new_schema': new_schema,
                'compatibility_type': compatibility_type,
                'timestamp': datetime.now().isoformat(),
                'platform': self.platform_name
            }

            # Emit schema evolution event
            self.emit_event('schema_evolved', evolution_event)

            # Create schema evolution node
            schema_node_id = f"{self.platform_name}_{topic_name}_schema_evolution_{datetime.now().isoformat()}"
            self.create_stream_node(
                node_id=schema_node_id,
                stream_type="schema_evolution",
                topic_name=topic_name,
                schema_evolution=evolution_event
            )

            logger.info(
                f"Tracked schema evolution for {topic_name}: {compatibility_type}")

    def get_stream_lineage(self, topic_name: str = None) -> Dict[str, Any]:
        """
        Get lineage graph for streaming data.

        Args:
            topic_name: Optional topic filter

        Returns:
            Streaming lineage information
        """
        # Filter nodes by platform and optionally by topic
        stream_nodes = []
        for node in self.tracker.get_all_nodes():
            if hasattr(node, 'platform') and node.platform == self.platform_name:
                if topic_name is None or (hasattr(node, 'topic_name') and node.topic_name == topic_name):
                    stream_nodes.append(node)

        return {
            'platform': self.platform_name,
            'topic_filter': topic_name,
            'node_count': len(stream_nodes),
            'nodes': [node.to_dict() for node in stream_nodes],
            'edges': self.tracker.get_edges_involving_nodes([node.node_id for node in stream_nodes])
        }

    def __str__(self) -> str:
        """String representation of streaming connector."""
        return f"{self.platform_name}Connector(connected={self.connected})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"{self.__class__.__name__}(platform='{self.platform_name}', "
                f"connected={self.connected}, auto_track={self.auto_track_lineage})")

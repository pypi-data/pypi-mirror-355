"""
Base class for streaming data connectors with lineage tracking.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Iterator, Callable, Union
from datetime import datetime
import json
import pandas as pd
from threading import Thread, Event
import queue

from ..core.dataframe_wrapper import LineageDataFrame

logger = logging.getLogger(__name__)


class StreamingConnector(ABC):
    """
    Abstract base class for streaming data connectors.

    Provides common functionality for streaming operations with lineage tracking,
    message processing patterns, and universal streaming patterns.
    """

    def __init__(self,
                 stream_name: str,
                 connection_config: Dict[str, Any] = None,
                 consumer_config: Dict[str, Any] = None,
                 producer_config: Dict[str, Any] = None,
                 **kwargs):
        """
        Initialize streaming connector.

        Args:
            stream_name: Stream/topic name
            connection_config: Connection configuration
            consumer_config: Consumer-specific configuration
            producer_config: Producer-specific configuration
            **kwargs: Additional connector options
        """
        self.stream_name = stream_name
        self.connection_config = connection_config or {}
        self.consumer_config = consumer_config or {}
        self.producer_config = producer_config or {}

        # Initialize tracker if provided
        from ..core.tracker import LineageTracker
        self.tracker = kwargs.get('tracker', LineageTracker())

        # Streaming state
        self.consumer = None
        self.producer = None
        self.is_consuming = False
        self.is_producing = False
        self.stop_event = Event()

        # Message processing
        self.batch_size = kwargs.get('batch_size', 100)
        self.timeout_ms = kwargs.get('timeout_ms', 1000)
        self.auto_commit = kwargs.get('auto_commit', True)
        self.message_format = kwargs.get(
            'message_format', 'json')  # json, avro, protobuf

        # Lineage tracking
        self.track_schema_evolution = kwargs.get(
            'track_schema_evolution', True)
        self.deduplicate_messages = kwargs.get('deduplicate_messages', False)
        self.message_buffer = queue.Queue(
            maxsize=kwargs.get('buffer_size', 10000))

    @abstractmethod
    def connect_consumer(self) -> None:
        """Establish consumer connection to streaming platform."""
        pass

    @abstractmethod
    def connect_producer(self) -> None:
        """Establish producer connection to streaming platform."""
        pass

    def disconnect(self) -> None:
        """Close streaming connections."""
        self.stop_consuming()
        self.stop_producing()

        if self.consumer:
            self.consumer = None
        if self.producer:
            self.producer = None

        logger.info(f"Disconnected from {self.__class__.__name__}")

    @abstractmethod
    def consume_messages(self, max_messages: int = None,
                         timeout_ms: int = None) -> List[Dict[str, Any]]:
        """
        Consume messages from stream.

        Args:
            max_messages: Maximum number of messages to consume
            timeout_ms: Timeout in milliseconds

        Returns:
            List of message dictionaries
        """
        pass

    @abstractmethod
    def produce_message(self, message: Dict[str, Any],
                        key: str = None,
                        partition: int = None) -> bool:
        """
        Produce message to stream.

        Args:
            message: Message data
            key: Message key for partitioning
            partition: Specific partition (if supported)

        Returns:
            True if message sent successfully
        """
        pass

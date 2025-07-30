"""
Apache Kafka connector for streaming data operations with lineage tracking.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

try:
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

from .streaming_base import StreamingConnector

logger = logging.getLogger(__name__)


class KafkaConnector(StreamingConnector):
    """
    Apache Kafka connector with comprehensive streaming operations.

    Features:
    - Full Kafka API integration with kafka-python
    - Producer and consumer support with configurable serialization
    - Consumer group management and offset handling
    - Schema registry integration support
    - Batch processing and real-time streaming
    - Automatic topic creation and partition management
    """

    def __init__(self,
                 topic_name: str,
                 bootstrap_servers: str = "localhost:9092",
                 consumer_group: str = None,
                 connection_config: Dict[str, Any] = None,
                 consumer_config: Dict[str, Any] = None,
                 producer_config: Dict[str, Any] = None,
                 **kwargs):
        """
        Initialize Kafka connector.

        Args:
            topic_name: Kafka topic name
            bootstrap_servers: Kafka bootstrap servers (comma-separated)
            consumer_group: Consumer group ID
            connection_config: Connection configuration
            consumer_config: Consumer-specific configuration
            producer_config: Producer-specific configuration
            **kwargs: Additional connector options
        """
        if not KAFKA_AVAILABLE:
            raise ImportError(
                "kafka-python is required for Kafka connector. Install with: pip install kafka-python")

        # Set up connection config
        connection_config = connection_config or {}
        connection_config['bootstrap_servers'] = bootstrap_servers.split(',')

        super().__init__(
            stream_name=topic_name,
            connection_config=connection_config,
            consumer_config=consumer_config,
            producer_config=producer_config,
            **kwargs
        )

        self.topic_name = topic_name
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group = consumer_group or f"lineagepy_consumer_{abs(hash(topic_name))}"

        # Kafka-specific configuration
        self.key_serializer = kwargs.get('key_serializer', 'str')
        self.value_serializer = kwargs.get('value_serializer', 'json')
        self.key_deserializer = kwargs.get('key_deserializer', 'str')
        self.value_deserializer = kwargs.get('value_deserializer', 'json')

        # Consumer settings
        self.auto_offset_reset = kwargs.get('auto_offset_reset', 'latest')
        self.enable_auto_commit = kwargs.get('enable_auto_commit', True)
        self.auto_commit_interval_ms = kwargs.get(
            'auto_commit_interval_ms', 5000)

        # Producer settings
        self.compression_type = kwargs.get('compression_type', None)
        self.batch_size_bytes = kwargs.get('batch_size_bytes', 16384)
        self.linger_ms = kwargs.get('linger_ms', 0)
        self.acks = kwargs.get('acks', 1)

    def connect_consumer(self) -> None:
        """Establish Kafka consumer connection."""
        try:
            # Prepare consumer configuration
            consumer_config = {
                'bootstrap_servers': self.connection_config['bootstrap_servers'],
                'group_id': self.consumer_group,
                'auto_offset_reset': self.auto_offset_reset,
                'enable_auto_commit': self.enable_auto_commit,
                'auto_commit_interval_ms': self.auto_commit_interval_ms,
                'consumer_timeout_ms': self.timeout_ms,
                'api_version': (0, 10, 1),
                **self.consumer_config
            }

            # Set up deserializers
            if self.value_deserializer == 'json':
                consumer_config['value_deserializer'] = lambda x: json.loads(
                    x.decode('utf-8')) if x else None
            elif self.value_deserializer == 'str':
                consumer_config['value_deserializer'] = lambda x: x.decode(
                    'utf-8') if x else None

            if self.key_deserializer == 'str':
                consumer_config['key_deserializer'] = lambda x: x.decode(
                    'utf-8') if x else None

            # Create consumer
            self.consumer = KafkaConsumer(**consumer_config)

            # Subscribe to topic
            self.consumer.subscribe([self.topic_name])

            logger.info(
                f"Connected Kafka consumer to topic: {self.topic_name}, group: {self.consumer_group}")

        except Exception as e:
            logger.error(f"Failed to connect Kafka consumer: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Kafka consumer: {str(e)}")

    def connect_producer(self) -> None:
        """Establish Kafka producer connection."""
        try:
            # Prepare producer configuration
            producer_config = {
                'bootstrap_servers': self.connection_config['bootstrap_servers'],
                'acks': self.acks,
                'compression_type': self.compression_type,
                'batch_size': self.batch_size_bytes,
                'linger_ms': self.linger_ms,
                'api_version': (0, 10, 1),
                **self.producer_config
            }

            # Set up serializers
            if self.value_serializer == 'json':
                producer_config['value_serializer'] = lambda x: json.dumps(
                    x).encode('utf-8')
            elif self.value_serializer == 'str':
                producer_config['value_serializer'] = lambda x: str(
                    x).encode('utf-8')

            if self.key_serializer == 'str':
                producer_config['key_serializer'] = lambda x: str(
                    x).encode('utf-8') if x else None

            # Create producer
            self.producer = KafkaProducer(**producer_config)

            logger.info(
                f"Connected Kafka producer to topic: {self.topic_name}")

        except Exception as e:
            logger.error(f"Failed to connect Kafka producer: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Kafka producer: {str(e)}")

    def consume_messages(self, max_messages: int = None,
                         timeout_ms: int = None) -> List[Dict[str, Any]]:
        """
        Consume messages from Kafka topic.

        Args:
            max_messages: Maximum number of messages to consume
            timeout_ms: Timeout in milliseconds

        Returns:
            List of message dictionaries
        """
        if not self.consumer:
            self.connect_consumer()

        max_messages = max_messages or self.batch_size
        timeout_ms = timeout_ms or self.timeout_ms

        messages = []

        try:
            # Poll for messages
            msg_pack = self.consumer.poll(
                timeout_ms=timeout_ms, max_records=max_messages)

            for topic_partition, msgs in msg_pack.items():
                for msg in msgs:
                    message_data = {
                        'key': msg.key,
                        'value': msg.value,
                        'offset': msg.offset,
                        'partition': msg.partition,
                        'timestamp': datetime.fromtimestamp(msg.timestamp / 1000) if msg.timestamp else None,
                        'topic': msg.topic,
                        'headers': dict(msg.headers or [])
                    }
                    messages.append(message_data)

            if messages:
                logger.info(
                    f"Consumed {len(messages)} messages from Kafka topic: {self.topic_name}")

            return messages

        except Exception as e:
            logger.error(f"Failed to consume Kafka messages: {str(e)}")
            raise

    def produce_message(self, message: Dict[str, Any],
                        key: str = None,
                        partition: int = None) -> bool:
        """
        Produce message to Kafka topic.

        Args:
            message: Message data
            key: Message key for partitioning
            partition: Specific partition

        Returns:
            True if message sent successfully
        """
        if not self.producer:
            self.connect_producer()

        try:
            # Prepare message for sending
            headers = message.pop('_headers', None)
            timestamp_ms = message.pop('_timestamp', None)

            # Send message
            future = self.producer.send(
                self.topic_name,
                value=message,
                key=key,
                partition=partition,
                headers=list(headers.items()) if headers else None,
                timestamp_ms=timestamp_ms
            )

            # Wait for send to complete (synchronous)
            record_metadata = future.get(timeout=10)

            logger.debug(f"Message sent to Kafka topic: {record_metadata.topic}, "
                         f"partition: {record_metadata.partition}, offset: {record_metadata.offset}")

            return True

        except Exception as e:
            logger.error(f"Failed to produce Kafka message: {str(e)}")
            return False

    def produce_batch(self, messages: List[Dict[str, Any]],
                      keys: List[str] = None) -> Dict[str, Any]:
        """
        Produce batch of messages to Kafka topic.

        Args:
            messages: List of message data
            keys: List of message keys (optional)

        Returns:
            Production results dictionary
        """
        if not self.producer:
            self.connect_producer()

        results = {
            'total_messages': len(messages),
            'successful': 0,
            'failed': 0,
            'errors': []
        }

        futures = []

        try:
            # Send all messages asynchronously
            for i, message in enumerate(messages):
                key = keys[i] if keys and i < len(keys) else None

                try:
                    future = self.producer.send(
                        self.topic_name,
                        value=message,
                        key=key
                    )
                    futures.append((i, future))

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Message {i}: {str(e)}")

            # Wait for all sends to complete
            for i, future in futures:
                try:
                    future.get(timeout=10)
                    results['successful'] += 1
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Message {i}: {str(e)}")

            # Flush producer to ensure all messages are sent
            self.producer.flush()

            logger.info(f"Produced batch to Kafka: {results['successful']} successful, "
                        f"{results['failed']} failed")

            return results

        except Exception as e:
            logger.error(f"Failed to produce batch to Kafka: {str(e)}")
            raise

    def get_topic_metadata(self) -> Dict[str, Any]:
        """Get Kafka topic metadata and configuration."""
        try:
            if not self.consumer:
                self.connect_consumer()

            # Get topic metadata
            metadata = self.consumer.list_consumer_group_offsets()
            partitions = self.consumer.partitions_for_topic(self.topic_name)

            info = {
                'topic_name': self.topic_name,
                'partition_count': len(partitions) if partitions else 0,
                'partitions': list(partitions) if partitions else [],
                'consumer_group': self.consumer_group,
                'bootstrap_servers': self.bootstrap_servers
            }

            # Get partition information
            if partitions:
                partition_info = []
                for partition in partitions:
                    try:
                        # Get high water mark (latest offset)
                        tp = TopicPartition(self.topic_name, partition)
                        high_water_marks = self.consumer.highwater(tp)

                        partition_info.append({
                            'partition': partition,
                            'high_water_mark': high_water_marks
                        })
                    except:
                        partition_info.append({
                            'partition': partition,
                            'high_water_mark': None
                        })

                info['partition_details'] = partition_info

            return info

        except Exception as e:
            logger.error(f"Failed to get Kafka topic metadata: {str(e)}")
            return {'error': str(e)}

    def seek_to_beginning(self) -> None:
        """Seek consumer to beginning of all partitions."""
        if not self.consumer:
            self.connect_consumer()

        try:
            self.consumer.seek_to_beginning()
            logger.info(f"Seeking to beginning of topic: {self.topic_name}")
        except Exception as e:
            logger.error(f"Failed to seek to beginning: {str(e)}")
            raise

    def seek_to_end(self) -> None:
        """Seek consumer to end of all partitions."""
        if not self.consumer:
            self.connect_consumer()

        try:
            self.consumer.seek_to_end()
            logger.info(f"Seeking to end of topic: {self.topic_name}")
        except Exception as e:
            logger.error(f"Failed to seek to end: {str(e)}")
            raise

    def commit_offsets(self) -> None:
        """Manually commit current offsets."""
        if not self.consumer:
            return

        try:
            self.consumer.commit()
            logger.info("Committed Kafka offsets")
        except Exception as e:
            logger.error(f"Failed to commit offsets: {str(e)}")
            raise

    def _commit_offsets(self) -> None:
        """Internal offset commit for base class."""
        self.commit_offsets()

    def __str__(self) -> str:
        return f"KafkaConnector(topic='{self.topic_name}', servers='{self.bootstrap_servers}')"

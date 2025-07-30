"""
Real-time streaming and event-driven lineage integration for DataLineagePy.

This module provides comprehensive streaming data lineage tracking with support for:
- Apache Kafka with schema registry integration
- Apache Pulsar with multi-tenancy support
- AWS Kinesis with shard-level tracking
- Event-driven lineage updates
- Real-time visualization
- Stream processing framework integration
"""

import logging

logger = logging.getLogger(__name__)

# Core streaming components
try:
    from .streaming_base import StreamingConnector, StreamNode
    STREAMING_BASE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Streaming base components not available: {e}")
    STREAMING_BASE_AVAILABLE = False

# Kafka integration
try:
    from .kafka_lineage import KafkaLineageTracker
    KAFKA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Kafka integration not available: {e}")
    KAFKA_AVAILABLE = False

# Pulsar integration
try:
    from .pulsar_lineage import PulsarLineageTracker
    PULSAR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Pulsar integration not available: {e}")
    PULSAR_AVAILABLE = False

# Kinesis integration
try:
    from .kinesis_lineage import KinesisLineageTracker
    KINESIS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Kinesis integration not available: {e}")
    KINESIS_AVAILABLE = False

# Event-driven lineage
try:
    from .event_lineage import EventLineageTracker
    EVENT_LINEAGE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Event-driven lineage not available: {e}")
    EVENT_LINEAGE_AVAILABLE = False

# Universal stream manager
try:
    from .universal_stream_manager import UniversalStreamManager
    UNIVERSAL_MANAGER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Universal stream manager not available: {e}")
    UNIVERSAL_MANAGER_AVAILABLE = False

# Live dashboard
try:
    from .live_dashboard import LiveLineageDashboard
    LIVE_DASHBOARD_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Live dashboard not available: {e}")
    LIVE_DASHBOARD_AVAILABLE = False

# Stream processing integrations
try:
    from .flink_integration import FlinkLineageTracker
    FLINK_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Flink integration not available: {e}")
    FLINK_AVAILABLE = False

try:
    from .kafka_streams_integration import KafkaStreamsTracker
    KAFKA_STREAMS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Kafka Streams integration not available: {e}")
    KAFKA_STREAMS_AVAILABLE = False

# Testing framework
try:
    from .testing import StreamTestFramework
    STREAM_TESTING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Stream testing framework not available: {e}")
    STREAM_TESTING_AVAILABLE = False

# Export all available components
__all__ = []

if STREAMING_BASE_AVAILABLE:
    __all__.extend(['StreamingConnector', 'StreamNode'])

if KAFKA_AVAILABLE:
    __all__.append('KafkaLineageTracker')

if PULSAR_AVAILABLE:
    __all__.append('PulsarLineageTracker')

if KINESIS_AVAILABLE:
    __all__.append('KinesisLineageTracker')

if EVENT_LINEAGE_AVAILABLE:
    __all__.append('EventLineageTracker')

if UNIVERSAL_MANAGER_AVAILABLE:
    __all__.append('UniversalStreamManager')

if LIVE_DASHBOARD_AVAILABLE:
    __all__.append('LiveLineageDashboard')

if FLINK_AVAILABLE:
    __all__.append('FlinkLineageTracker')

if KAFKA_STREAMS_AVAILABLE:
    __all__.append('KafkaStreamsTracker')

if STREAM_TESTING_AVAILABLE:
    __all__.append('StreamTestFramework')

# Availability check functions


def check_kafka_available():
    """Check if Kafka dependencies are available."""
    try:
        import kafka
        return True
    except ImportError:
        return False


def check_pulsar_available():
    """Check if Pulsar dependencies are available."""
    try:
        import pulsar
        return True
    except ImportError:
        return False


def check_kinesis_available():
    """Check if Kinesis dependencies are available."""
    try:
        import boto3
        return True
    except ImportError:
        return False


def get_available_platforms():
    """Get list of available streaming platforms."""
    platforms = []

    if check_kafka_available():
        platforms.append('kafka')

    if check_pulsar_available():
        platforms.append('pulsar')

    if check_kinesis_available():
        platforms.append('kinesis')

    return platforms


def print_streaming_status():
    """Print status of streaming platform availability."""
    print("DataLineagePy Streaming Integration Status:")
    print("=" * 45)

    platforms = [
        ('Kafka', check_kafka_available()),
        ('Pulsar', check_pulsar_available()),
        ('Kinesis', check_kinesis_available()),
    ]

    for platform, available in platforms:
        status = "✅ Available" if available else "❌ Not Available"
        print(f"{platform:10} : {status}")

    available_count = sum(1 for _, available in platforms if available)
    print(f"\nTotal Available: {available_count}/{len(platforms)} platforms")

    if available_count == 0:
        print("\n💡 Install streaming dependencies:")
        print("   pip install kafka-python")
        print("   pip install pulsar-client")
        print("   pip install boto3")


# Module metadata
__version__ = "8.0.0"
__author__ = "DataLineagePy Team"
__description__ = "Real-time streaming lineage integration"

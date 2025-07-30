"""
Tests for cloud storage and streaming connectors.

This module contains unit tests for:
- CloudStorageConnector base class
- S3Connector
- StreamingConnector base class  
- KafkaConnector
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import tempfile
import os
from datetime import datetime

from lineagepy.core.tracker import LineageTracker


class TestCloudStorageConnector(unittest.TestCase):
    """Test CloudStorageConnector base class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = LineageTracker()

    @patch('lineagepy.connectors.cloud_base.CloudStorageConnector.__abstractmethods__', set())
    def test_cloud_storage_initialization(self):
        """Test CloudStorageConnector initialization."""
        from lineagepy.connectors.cloud_base import CloudStorageConnector

        connector = CloudStorageConnector(
            bucket_name='test-bucket',
            region='us-east-1',
            tracker=self.tracker
        )

        self.assertEqual(connector.bucket_name, 'test-bucket')
        self.assertEqual(connector.region, 'us-east-1')
        self.assertEqual(connector.tracker, self.tracker)
        self.assertIsNone(connector.connection)


class TestS3Connector(unittest.TestCase):
    """Test S3Connector functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = LineageTracker()

    def test_s3_connector_import_error(self):
        """Test S3Connector behavior when boto3 is not available."""
        with patch.dict('sys.modules', {'boto3': None}):
            with patch('lineagepy.connectors.s3.S3_AVAILABLE', False):
                from lineagepy.connectors.s3 import S3Connector

                with self.assertRaises(ImportError) as context:
                    S3Connector('test-bucket')

                self.assertIn('boto3 is required', str(context.exception))

    @patch('lineagepy.connectors.s3.S3_AVAILABLE', True)
    @patch('lineagepy.connectors.s3.boto3')
    def test_s3_connector_initialization(self, mock_boto3):
        """Test S3Connector initialization."""
        from lineagepy.connectors.s3 import S3Connector

        connector = S3Connector(
            bucket_name='test-bucket',
            region='us-west-2',
            tracker=self.tracker
        )

        self.assertEqual(connector.bucket_name, 'test-bucket')
        self.assertEqual(connector.region, 'us-west-2')
        self.assertIsNone(connector.s3_client)


class TestKafkaConnector(unittest.TestCase):
    """Test KafkaConnector functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = LineageTracker()

    def test_kafka_connector_import_error(self):
        """Test KafkaConnector behavior when kafka-python is not available."""
        with patch.dict('sys.modules', {'kafka': None}):
            with patch('lineagepy.connectors.kafka.KAFKA_AVAILABLE', False):
                from lineagepy.connectors.kafka import KafkaConnector

                with self.assertRaises(ImportError) as context:
                    KafkaConnector('test-topic')

                self.assertIn('kafka-python is required',
                              str(context.exception))

    @patch('lineagepy.connectors.kafka.KAFKA_AVAILABLE', True)
    @patch('lineagepy.connectors.kafka.KafkaProducer')
    @patch('lineagepy.connectors.kafka.KafkaConsumer')
    def test_kafka_connector_initialization(self, mock_consumer, mock_producer):
        """Test KafkaConnector initialization."""
        from lineagepy.connectors.kafka import KafkaConnector

        connector = KafkaConnector(
            topic_name='test-topic',
            bootstrap_servers='localhost:9092',
            consumer_group='test-group',
            tracker=self.tracker
        )

        self.assertEqual(connector.topic_name, 'test-topic')
        self.assertEqual(connector.bootstrap_servers, 'localhost:9092')
        self.assertEqual(connector.consumer_group, 'test-group')
        self.assertEqual(connector.stream_name, 'test-topic')


if __name__ == '__main__':
    unittest.main()

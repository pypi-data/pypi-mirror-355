#!/usr/bin/env python3
"""
DataLineagePy Phase 3: Cloud & Streaming Ecosystem Demo

This example demonstrates the cloud storage and streaming capabilities
added in Phase 3, including AWS S3 integration and Apache Kafka streaming
with comprehensive lineage tracking.

Key Features Demonstrated:
- AWS S3 cloud storage operations with lineage
- Apache Kafka streaming with real-time lineage tracking
- Cross-platform data movement (cloud to streaming)
- Advanced lineage visualization for distributed systems
- Schema evolution tracking in streaming contexts

Requirements:
- pip install data-lineage-py[cloud,streaming]
- AWS credentials configured (for S3 demo)
- Kafka cluster running (for streaming demo)
"""

from lineagepy.connectors import S3Connector, KafkaConnector
from lineagepy.core.tracker import LineageTracker
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
import time
import threading

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# DataLineagePy imports


def create_sample_datasets():
    """Create sample datasets for cloud and streaming demos."""
    print("🔧 Creating sample datasets...")

    # Customer data for S3 storage
    customers = pd.DataFrame({
        'customer_id': range(1, 1001),
        'name': [f'Customer_{i}' for i in range(1, 1001)],
        'email': [f'customer{i}@example.com' for i in range(1, 1001)],
        'signup_date': pd.date_range('2023-01-01', periods=1000),
        'region': np.random.choice(['US', 'EU', 'ASIA'], 1000),
        'tier': np.random.choice(['Bronze', 'Silver', 'Gold', 'Platinum'], 1000)
    })

    # Order events for streaming
    orders = pd.DataFrame({
        'order_id': range(1, 501),
        'customer_id': np.random.randint(1, 1001, 500),
        'product_id': np.random.randint(1, 101, 500),
        'quantity': np.random.randint(1, 6, 500),
        'price': np.random.uniform(10, 500, 500).round(2),
        'order_timestamp': pd.date_range('2024-01-01', periods=500, freq='1H'),
        'status': np.random.choice(['pending', 'confirmed', 'shipped', 'delivered'], 500)
    })

    # Product catalog
    products = pd.DataFrame({
        'product_id': range(1, 101),
        'name': [f'Product_{i}' for i in range(1, 101)],
        'category': np.random.choice(['Electronics', 'Clothing', 'Books', 'Home'], 100),
        'price': np.random.uniform(5, 1000, 100).round(2),
        'in_stock': np.random.choice([True, False], 100)
    })

    return customers, orders, products


def demo_s3_operations():
    """Demonstrate AWS S3 cloud storage operations with lineage."""
    print("\n🌩️  AWS S3 CLOUD STORAGE DEMO")
    print("=" * 50)

    try:
        # Initialize lineage tracker
        tracker = LineageTracker()

        # Configure S3 connector (replace with your bucket)
        s3_connector = S3Connector(
            bucket_name='my-data-lineage-bucket',  # Replace with your bucket
            region='us-east-1',
            tracker=tracker
        )

        print("🔗 Connecting to S3...")

        # Test connection (will work if credentials are configured)
        try:
            s3_connector.connect()
            print("✅ S3 connection successful!")

            # Create sample data
            customers, orders, products = create_sample_datasets()

            # Upload datasets to S3 with lineage tracking
            print("\n📤 Uploading datasets to S3...")

            # Save locally first (would be temp files in real scenario)
            customers.to_parquet('customers.parquet', index=False)
            orders.to_csv('orders.csv', index=False)
            products.to_json('products.json', orient='records')

            # Upload to S3
            s3_connector.upload_object(
                'customers.parquet', 'data/customers.parquet')
            s3_connector.upload_object('orders.csv', 'data/orders.csv')
            s3_connector.upload_object('products.json', 'data/products.json')

            print("✅ Datasets uploaded to S3!")

            # Read data back from S3 with lineage tracking
            print("\n📥 Reading data from S3 with lineage tracking...")

            # Read Parquet from S3
            customers_df = s3_connector.read_parquet('data/customers.parquet')
            print(f"📊 Customers from S3: {customers_df.shape}")

            # Read CSV from S3
            orders_df = s3_connector.read_csv('data/orders.csv')
            print(f"📊 Orders from S3: {orders_df.shape}")

            # Perform analysis with lineage tracking
            print("\n🔍 Performing analysis with lineage tracking...")

            # Customer analysis
            gold_customers = customers_df[customers_df['tier'] == 'Gold']
            regional_summary = customers_df.groupby(
                'region').size().reset_index(name='customer_count')

            # Order analysis
            order_summary = orders_df.groupby('status').agg({
                'quantity': 'sum',
                'price': 'mean'
            }).reset_index()

            print(f"✅ Analysis complete!")
            print(f"   - Gold customers: {len(gold_customers)}")
            print(f"   - Regional summary: {len(regional_summary)} regions")
            print(f"   - Order summary: {len(order_summary)} statuses")

            # Display lineage graph
            print("\n📈 S3 Lineage Graph:")
            lineage_summary = tracker.get_lineage_summary()
            print(f"   - Nodes: {lineage_summary['total_nodes']}")
            print(f"   - Edges: {lineage_summary['total_edges']}")
            print(
                f"   - Cloud objects: {sum(1 for n in tracker.nodes.values() if 'Cloud' in str(type(n)))}")

            # Clean up temp files
            import os
            for file in ['customers.parquet', 'orders.csv', 'products.json']:
                if os.path.exists(file):
                    os.remove(file)

        except Exception as e:
            print(f"⚠️  S3 demo requires AWS credentials: {str(e)}")
            print("   Configure AWS CLI or set environment variables:")
            print("   - AWS_ACCESS_KEY_ID")
            print("   - AWS_SECRET_ACCESS_KEY")
            print("   - AWS_DEFAULT_REGION")

    except ImportError as e:
        print(f"⚠️  S3 demo requires boto3: {str(e)}")
        print("   Install with: pip install data-lineage-py[aws]")


def demo_kafka_streaming():
    """Demonstrate Apache Kafka streaming operations with lineage."""
    print("\n🌊 APACHE KAFKA STREAMING DEMO")
    print("=" * 50)

    try:
        # Initialize lineage tracker
        tracker = LineageTracker()

        # Configure Kafka connector
        kafka_connector = KafkaConnector(
            topic_name='customer-events',
            bootstrap_servers='localhost:9092',
            consumer_group='lineagepy_demo',
            tracker=tracker
        )

        print("🔗 Connecting to Kafka...")

        try:
            # Test connection
            kafka_connector.connect_producer()
            kafka_connector.connect_consumer()
            print("✅ Kafka connection successful!")

            # Create sample streaming events
            print("\n📡 Generating sample streaming events...")

            events = []
            for i in range(50):
                event = {
                    'event_id': f'evt_{i:04d}',
                    'customer_id': np.random.randint(1, 1001),
                    'event_type': np.random.choice(['login', 'purchase', 'view', 'logout']),
                    'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
                    'metadata': {
                        'ip_address': f'192.168.1.{np.random.randint(1, 255)}',
                        'user_agent': 'DataLineagePy/1.0'
                    }
                }
                events.append(event)

            # Produce events to Kafka
            print(f"📤 Producing {len(events)} events to Kafka...")

            for event in events[:10]:  # Produce first 10 events
                kafka_connector.produce_message(
                    event, key=str(event['customer_id']))
                time.sleep(0.1)  # Small delay

            print("✅ Events produced to Kafka!")

            # Consume events with lineage tracking
            print("\n📥 Consuming events with lineage tracking...")

            # Consume to DataFrame
            events_df = kafka_connector.consume_to_dataframe(
                max_messages=10, timeout_ms=5000)

            if len(events_df) > 0:
                print(f"📊 Consumed events: {events_df.shape}")

                # Analyze streaming data
                print("\n🔍 Analyzing streaming data...")

                # Event type distribution
                event_type_dist = events_df['event_type'].value_counts(
                ).reset_index()
                event_type_dist.columns = ['event_type', 'count']

                # Customer activity
                customer_activity = events_df.groupby(
                    'customer_id').size().reset_index(name='event_count')

                print(f"✅ Streaming analysis complete!")
                print(f"   - Event types: {len(event_type_dist)}")
                print(f"   - Active customers: {len(customer_activity)}")

                # Display lineage information
                print("\n📈 Kafka Streaming Lineage:")
                lineage_summary = tracker.get_lineage_summary()
                print(
                    f"   - Stream nodes: {sum(1 for n in tracker.nodes.values() if 'Stream' in str(type(n)))}")
                print(
                    f"   - Total operations: {lineage_summary['total_edges']}")

            else:
                print("⚠️  No events consumed (topic may be empty)")

        except Exception as e:
            print(f"⚠️  Kafka demo requires running Kafka cluster: {str(e)}")
            print("   Start Kafka locally or use cloud Kafka service")
            print("   Default connection: localhost:9092")

    except ImportError as e:
        print(f"⚠️  Kafka demo requires kafka-python: {str(e)}")
        print("   Install with: pip install data-lineage-py[kafka]")


def demo_cross_platform_pipeline():
    """Demonstrate cross-platform data pipeline (S3 → Processing → Kafka)."""
    print("\n🌐 CROSS-PLATFORM PIPELINE DEMO")
    print("=" * 50)

    print("🔄 Simulating cross-platform data pipeline:")
    print("   S3 (Storage) → Processing → Kafka (Streaming)")

    try:
        # Initialize tracker for full pipeline lineage
        tracker = LineageTracker()

        # Create mock data representing S3 source
        print("\n1️⃣ Simulating S3 data source...")
        s3_data = pd.DataFrame({
            'user_id': range(1, 101),
            'action': np.random.choice(['click', 'view', 'purchase'], 100),
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='1H'),
            'value': np.random.uniform(1, 100, 100)
        })

        # Process data (transformation step)
        print("2️⃣ Processing and transforming data...")
        processed_data = s3_data.copy()
        processed_data['processed_timestamp'] = datetime.now()
        processed_data['value_normalized'] = (
            processed_data['value'] - processed_data['value'].mean()) / processed_data['value'].std()

        # Aggregate for streaming
        aggregated = processed_data.groupby('action').agg({
            'value': ['count', 'mean', 'sum'],
            'value_normalized': 'mean'
        }).round(2)
        aggregated.columns = ['_'.join(col).strip()
                              for col in aggregated.columns]
        aggregated = aggregated.reset_index()

        print(
            f"✅ Data processed: {len(s3_data)} → {len(aggregated)} aggregated records")

        # Simulate streaming output
        print("3️⃣ Preparing for streaming output...")

        streaming_events = []
        for _, row in aggregated.iterrows():
            event = {
                'action_type': row['action'],
                'metrics': {
                    'count': int(row['value_count']),
                    'mean_value': float(row['value_mean']),
                    'total_value': float(row['value_sum']),
                    'normalized_mean': float(row['value_normalized_mean'])
                },
                'pipeline_timestamp': datetime.now().isoformat(),
                'source': 's3_processed'
            }
            streaming_events.append(event)

        print(
            f"✅ Pipeline complete: {len(streaming_events)} events ready for streaming")

        # Display pipeline lineage
        print("\n📈 Cross-Platform Pipeline Lineage:")
        print("   S3 Data Source")
        print("   ↓ (read)")
        print("   Data Processing")
        print("   ↓ (transform)")
        print("   Aggregation")
        print("   ↓ (stream)")
        print("   Kafka Topic")

        # Show sample event
        print(f"\n📄 Sample streaming event:")
        print(json.dumps(streaming_events[0], indent=2))

    except Exception as e:
        print(f"⚠️  Cross-platform demo error: {str(e)}")


def main():
    """Run the comprehensive Phase 3 demo."""
    print("🚀 DataLineagePy Phase 3: Cloud & Streaming Ecosystem")
    print("=" * 60)
    print("Demonstrating cloud storage, streaming, and distributed data lineage")
    print()

    # Run individual demos
    demo_s3_operations()
    demo_kafka_streaming()
    demo_cross_platform_pipeline()

    print("\n🎉 Phase 3 Demo Complete!")
    print("\n📚 Key Takeaways:")
    print("   ✅ Cloud storage integration with AWS S3")
    print("   ✅ Streaming data processing with Apache Kafka")
    print("   ✅ Real-time data lineage tracking")
    print("   ✅ Cross-platform data pipeline lineage")
    print("   ✅ Advanced lineage visualization")

    print("\n🔗 Next Steps:")
    print("   - Configure AWS credentials for S3 demo")
    print("   - Start Kafka cluster for streaming demo")
    print("   - Explore additional cloud providers (GCP, Azure)")
    print("   - Try advanced streaming platforms (Pulsar, Kinesis)")
    print("   - Implement data lake formats (Delta, Iceberg)")


if __name__ == "__main__":
    main()

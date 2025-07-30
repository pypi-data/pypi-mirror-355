"""
Phase 4 Visualization Demo for DataLineagePy.
"""

from lineagepy import LineageDataFrame, LineageTracker
from lineagepy.visualization.graph_visualizer import LineageGraphVisualizer
from lineagepy.visualization.exporters import JSONExporter, HTMLExporter


def main():
    print("🎨 DataLineagePy Phase 4 Visualization Demo")
    print("=" * 45)

    # Reset tracker
    LineageTracker.reset_global_instance()

    # Create e-commerce data
    sales_data = {
        'product': ['Laptop', 'Mouse', 'Keyboard'],
        'price': [999.99, 29.99, 79.99],
        'quantity': [2, 5, 3],
        'category': ['Electronics', 'Accessories', 'Accessories']
    }

    customer_data = {
        'customer_id': [1, 2, 3],
        'tier': ['Gold', 'Silver', 'Bronze'],
        'region': ['North', 'South', 'East']
    }

    # Create DataFrames
    sales_df = LineageDataFrame(
        sales_data, name="sales", source_type="database")
    customers_df = LineageDataFrame(
        customer_data, name="customers", source_type="database")

    print(f"Sales data: {sales_df.shape}")
    print(f"Customer data: {customers_df.shape}")

    # Transform data
    sales_with_revenue = sales_df.assign(
        revenue=lambda x: x['price'] * x['quantity']
    )

    category_summary = sales_with_revenue.groupby('category').agg({
        'revenue': 'sum',
        'quantity': 'sum'
    })

    print(f"Revenue calculations: {sales_with_revenue.shape}")
    print(f"Category summary: {category_summary.shape}")

    # Analyze lineage
    visualizer = LineageGraphVisualizer()
    summary = visualizer.get_lineage_summary()

    print(f"\nLineage Summary:")
    print(f"  Nodes: {summary['total_nodes']}")
    print(f"  Transformations: {summary['total_edges']}")
    print(f"  Is DAG: {summary['is_dag']}")

    # Export results
    json_exporter = JSONExporter()
    html_exporter = HTMLExporter()

    json_file = json_exporter.export("demo_lineage.json")
    html_file = html_exporter.export("demo_report.html")

    print(f"\nExported:")
    print(f"  JSON: demo_lineage.json")
    print(f"  HTML: demo_report.html")

    print("\n✅ Phase 4 demo completed successfully!")


if __name__ == "__main__":
    main()

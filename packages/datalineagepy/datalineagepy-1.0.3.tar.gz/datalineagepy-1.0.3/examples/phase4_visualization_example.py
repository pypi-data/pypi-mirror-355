"""
Comprehensive example demonstrating DataLineagePy Phase 4 visualization features.

This example showcases:
- Interactive graph visualizations
- Column-level dependency analysis
- Comprehensive reporting
- Multiple export formats
- Real-world data pipeline visualization
"""

import tempfile
from pathlib import Path

from lineagepy import LineageDataFrame, LineageTracker

# Import visualization components (with graceful fallback)
try:
    from lineagepy.visualization.graph_visualizer import LineageGraphVisualizer
    from lineagepy.visualization.column_visualizer import ColumnLineageVisualizer
    from lineagepy.visualization.report_generator import LineageReportGenerator
    from lineagepy.visualization.exporters import (
        JSONExporter, HTMLExporter, CSVExporter, MarkdownExporter
    )
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False


def main():
    print("🎨 DataLineagePy Phase 4 Visualization Features Demo")
    print("=" * 55)

    if not HAS_VISUALIZATION:
        print("⚠️  Visualization modules not available.")
        print("   Install with: pip install 'datalineagepy[visualization]'")
        return

    # Reset tracker for clean demo
    LineageTracker.reset_global_instance()

    # 1. Create comprehensive e-commerce dataset
    print("\n1. Creating comprehensive e-commerce dataset...")

    # Orders data
    orders_data = {
        'order_id': [1001, 1002, 1003, 1004, 1005, 1006],
        'customer_id': [201, 202, 203, 201, 204, 202],
        'product_id': ['P001', 'P002', 'P003', 'P001', 'P004', 'P002'],
        'order_date': ['2023-01-15', '2023-01-16', '2023-01-17', '2023-01-18', '2023-01-19', '2023-01-20'],
        'quantity': [2, 1, 3, 1, 2, 4],
        'unit_price': [29.99, 149.99, 19.99, 29.99, 89.99, 149.99],
        'discount_percent': [10, 0, 15, 5, 0, 20]
    }

    # Customer data
    customers_data = {
        'customer_id': [201, 202, 203, 204],
        'customer_name': ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson'],
        'customer_tier': ['Gold', 'Silver', 'Bronze', 'Gold'],
        'region': ['North', 'South', 'East', 'West'],
        'signup_date': ['2022-03-15', '2022-07-20', '2023-01-10', '2021-11-05']
    }

    # Product data
    products_data = {
        'product_id': ['P001', 'P002', 'P003', 'P004'],
        'product_name': ['Wireless Headphones', 'Laptop Stand', 'Phone Case', 'Bluetooth Speaker'],
        'category': ['Electronics', 'Accessories', 'Accessories', 'Electronics'],
        'cost_price': [15.00, 75.00, 5.00, 45.00],
        'margin_percent': [100, 100, 300, 100]
    }

    # Create LineageDataFrames
    orders_df = LineageDataFrame(
        orders_data, name="orders", source_type="database", source_location="orders_table")
    customers_df = LineageDataFrame(
        customers_data, name="customers", source_type="database", source_location="customers_table")
    products_df = LineageDataFrame(
        products_data, name="products", source_type="database", source_location="products_table")

    print(f"   📊 Orders: {orders_df.shape}")
    print(f"   👥 Customers: {customers_df.shape}")
    print(f"   📦 Products: {products_df.shape}")

    # 2. Complex data transformation pipeline
    print("\n2. Executing complex data transformation pipeline...")

    # Step 1: Calculate order financials
    orders_financial = orders_df.assign(
        gross_amount=lambda x: x['quantity'] * x['unit_price'],
        discount_amount=lambda x: x['gross_amount'] *
        x['discount_percent'] / 100,
        net_amount=lambda x: x['gross_amount'] - x['discount_amount']
    )
    print(f"   💰 Added financial calculations: {orders_financial.shape}")

    # Step 2: Enrich with customer data
    orders_enriched = orders_financial.merge(
        customers_df,
        on='customer_id',
        how='left'
    )
    print(f"   🔗 Merged with customers: {orders_enriched.shape}")

    # Step 3: Add product information
    orders_complete = orders_enriched.merge(
        products_df,
        on='product_id',
        how='left'
    )
    print(f"   📦 Added product details: {orders_complete.shape}")

    # Step 4: Calculate profitability
    orders_with_profit = orders_complete.assign(
        cost_total=lambda x: x['quantity'] * x['cost_price'],
        profit_amount=lambda x: x['net_amount'] - x['cost_total'],
        profit_margin=lambda x: (
            x['profit_amount'] / x['net_amount'] * 100).round(2)
    )
    print(f"   📈 Added profitability metrics: {orders_with_profit.shape}")

    # Step 5: Customer analytics
    customer_analytics = orders_with_profit.groupby(['customer_id', 'customer_name', 'customer_tier']).agg({
        'net_amount': ['sum', 'mean', 'count'],
        'profit_amount': 'sum',
        'quantity': 'sum'
    }).reset_index()
    print(f"   👥 Customer analytics: {customer_analytics.shape}")

    # Step 6: Product performance analysis
    product_performance = orders_with_profit.groupby(['category', 'product_name']).agg({
        'quantity': 'sum',
        'net_amount': 'sum',
        'profit_amount': 'sum'
    }).reset_index()

    # Add performance metrics
    product_performance = product_performance.assign(
        avg_order_value=lambda x: x['net_amount'] / x['quantity'],
        profit_per_unit=lambda x: x['profit_amount'] / x['quantity']
    )
    print(f"   📦 Product performance: {product_performance.shape}")

    # Step 7: Regional analysis with pivot
    regional_analysis = orders_with_profit.pivot_table(
        values=['net_amount', 'profit_amount'],
        index='region',
        columns='category',
        aggfunc='sum',
        fill_value=0
    )
    print(f"   🌍 Regional analysis: {regional_analysis.shape}")

    # Step 8: Time series preparation (melt for analysis)
    time_series_data = orders_with_profit[['order_date', 'net_amount', 'profit_amount', 'quantity']].melt(
        id_vars=['order_date'],
        value_vars=['net_amount', 'profit_amount', 'quantity'],
        var_name='metric_type',
        value_name='metric_value'
    )
    print(f"   📅 Time series data: {time_series_data.shape}")

    # 3. Comprehensive lineage analysis
    print("\n3. Comprehensive Lineage Analysis")
    print("-" * 35)

    # Initialize visualizers
    graph_viz = LineageGraphVisualizer()
    column_viz = ColumnLineageVisualizer()
    report_gen = LineageReportGenerator()

    # Graph-level analysis
    graph_summary = graph_viz.get_lineage_summary()
    print(f"   📊 Graph Statistics:")
    print(f"      Total nodes: {graph_summary['total_nodes']}")
    print(f"      Total transformations: {graph_summary['total_edges']}")
    print(f"      Graph density: {graph_summary['graph_density']:.4f}")
    print(f"      Is valid DAG: {graph_summary['is_dag']}")
    print(
        f"      Connected components: {graph_summary['connected_components']}")

    # Node type breakdown
    print(f"\n   🔍 Node Types:")
    for node_type, count in graph_summary['node_types'].items():
        print(f"      {node_type}: {count}")

    # Transformation type breakdown
    print(f"\n   ⚙️ Transformation Types:")
    for trans_type, count in graph_summary['transformation_types'].items():
        print(f"      {trans_type}: {count}")

    # 4. Column-level impact analysis
    print("\n4. Column-Level Impact Analysis")
    print("-" * 32)

    # Analyze key business metrics
    key_columns = ['net_amount', 'profit_amount', 'profit_margin']

    for column in key_columns:
        impact = column_viz.get_column_impact_analysis(column)
        print(f"\n   📈 {column} Impact Analysis:")
        print(f"      Downstream columns: {len(impact['downstream_columns'])}")
        print(f"      Affected tables: {len(impact['affected_tables'])}")
        print(f"      Impact score: {impact['impact_score']}")
        if impact['downstream_columns']:
            print(
                f"      Dependencies: {', '.join(impact['downstream_columns'][:3])}{'...' if len(impact['downstream_columns']) > 3 else ''}")

    # 5. Generate comprehensive reports
    print("\n5. Generating Comprehensive Reports")
    print("-" * 35)

    # Summary report
    summary_report = report_gen.generate_summary_report()
    print(f"   📋 Summary Report Generated:")
    print(
        f"      Quality Score: {summary_report['quality_metrics']['completeness_score']:.2%}")
    print(
        f"      Context Coverage: {summary_report['quality_metrics']['context_coverage']:.2%}")
    print(
        f"      Column Mapping Coverage: {summary_report['quality_metrics']['column_mapping_coverage']:.2%}")

    # Column-specific reports
    column_reports = {}
    for column in ['profit_amount', 'net_amount']:
        column_reports[column] = report_gen.generate_column_report(column)
        print(
            f"   📊 {column} Report: {column_reports[column]['lineage']['total_dependencies']} dependencies")

    # 6. Export in multiple formats
    print("\n6. Exporting in Multiple Formats")
    print("-" * 33)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # JSON Export
        json_exporter = JSONExporter()
        json_file = json_exporter.export(
            str(temp_path / "ecommerce_lineage.json"))

        # HTML Report
        html_exporter = HTMLExporter()
        html_file = html_exporter.export(
            str(temp_path / "ecommerce_report.html"))

        # CSV Exports
        csv_exporter = CSVExporter()
        nodes_csv = csv_exporter.export_nodes(
            str(temp_path / "lineage_nodes.csv"))
        edges_csv = csv_exporter.export_edges(
            str(temp_path / "lineage_edges.csv"))

        # Markdown Summary
        md_exporter = MarkdownExporter()
        md_file = md_exporter.export(str(temp_path / "lineage_summary.md"))

        print(f"   📄 Generated Files:")
        print(f"      JSON: {Path(json_file).name}")
        print(f"      HTML: {Path(html_file).name}")
        print(f"      CSV: {Path(nodes_csv).name}, {Path(edges_csv).name}")
        print(f"      Markdown: {Path(md_file).name}")
        print(f"   📁 Location: {temp_dir}")

    # 7. Advanced lineage queries
    print("\n7. Advanced Lineage Queries")
    print("-" * 27)

    # Find paths between specific nodes
    tracker = LineageTracker.get_global_instance()

    # Get some node IDs for demonstration
    source_nodes = [node_id for node_id, node in tracker.nodes.items()
                    if getattr(node, 'source_type', '') == 'database'][:2]

    if len(source_nodes) >= 2:
        path = graph_viz.find_path_between_nodes(
            source_nodes[0], source_nodes[1])
        if path:
            print(f"   🛤️  Path found between nodes: {len(path)} steps")
        else:
            print(f"   🛤️  No direct path found between selected nodes")

    # Upstream/downstream analysis
    if source_nodes:
        sample_node = source_nodes[0]
        upstream = graph_viz.get_upstream_dependencies(sample_node)
        downstream = graph_viz.get_downstream_dependencies(sample_node)

        print(f"   ⬆️  Upstream dependencies: {len(upstream)}")
        print(f"   ⬇️  Downstream dependencies: {len(downstream)}")

    # 8. Visualization capabilities demonstration
    print("\n8. Visualization Capabilities")
    print("-" * 28)

    print("   🎨 Available Visualization Options:")
    print("      • Interactive Plotly graphs (if plotly installed)")
    print("      • Static Matplotlib plots (if matplotlib installed)")
    print("      • Graphviz diagrams (if graphviz installed)")
    print("      • NetworkX graph analysis")
    print("      • Column dependency diagrams")
    print("      • Multi-format exports (JSON, HTML, CSV, Markdown)")

    # Try to create a simple visualization
    try:
        # Create a simple plotly visualization (won't display in terminal)
        fig = graph_viz.visualize_with_plotly(
            include_columns=False,
            show_plot=False,
            save_html=None
        )
        if fig:
            print("   ✅ Plotly visualization created successfully")
        else:
            print("   ⚠️  Plotly not available")
    except Exception as e:
        print(f"   ⚠️  Visualization error: {str(e)[:50]}...")

    # 9. Performance and scalability insights
    print("\n9. Performance & Scalability Insights")
    print("-" * 37)

    print(f"   ⚡ Performance Metrics:")
    print(f"      Nodes tracked: {graph_summary['total_nodes']}")
    print(f"      Transformations: {graph_summary['total_edges']}")
    print(f"      Memory efficiency: Metadata-only tracking")
    print(f"      Thread safety: ✅ Enabled")
    print(
        f"      Graph complexity: {'Low' if graph_summary['graph_density'] < 0.1 else 'Medium' if graph_summary['graph_density'] < 0.3 else 'High'}")

    # 10. Integration recommendations
    print("\n10. Integration Recommendations")
    print("-" * 32)

    print("   🔧 For Production Use:")
    print("      • Enable selective column tracking for large datasets")
    print("      • Use export capabilities for lineage documentation")
    print("      • Integrate with CI/CD for automated lineage reports")
    print("      • Set up monitoring for lineage quality metrics")
    print("      • Consider visualization dashboards for stakeholders")

    print("\n✅ Phase 4 visualization demo completed!")
    print("\n💡 Key Features Demonstrated:")
    print("   • Comprehensive graph visualization and analysis")
    print("   • Column-level impact and dependency analysis")
    print("   • Multi-format reporting and export capabilities")
    print("   • Advanced lineage queries and path finding")
    print("   • Quality metrics and completeness scoring")
    print("   • Production-ready visualization tools")


if __name__ == "__main__":
    main()

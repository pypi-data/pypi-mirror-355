"""
Comprehensive Phase 4 Visualization Demo for DataLineagePy.

This demo showcases all visualization and reporting capabilities:
- Graph visualization and analysis
- Column-level impact analysis  
- Comprehensive reporting
- Multiple export formats
- Real-world data pipeline example
"""

import tempfile
from pathlib import Path

from lineagepy import LineageDataFrame, LineageTracker
from lineagepy.visualization.graph_visualizer import LineageGraphVisualizer
from lineagepy.visualization.column_visualizer import ColumnLineageVisualizer
from lineagepy.visualization.report_generator import LineageReportGenerator
from lineagepy.visualization.exporters import (
    JSONExporter, HTMLExporter, CSVExporter, MarkdownExporter
)


def main():
    print("🎨 DataLineagePy Phase 4 Comprehensive Visualization Demo")
    print("=" * 60)

    # Reset tracker for clean demo
    LineageTracker.reset_global_instance()

    # 1. Create realistic e-commerce dataset
    print("\n1. 📊 Creating E-commerce Dataset")
    print("-" * 35)

    # Sales transactions
    sales_data = {
        'transaction_id': [1001, 1002, 1003, 1004, 1005],
        'customer_id': [201, 202, 201, 203, 202],
        'product_id': ['P001', 'P002', 'P003', 'P001', 'P004'],
        'quantity': [2, 1, 3, 1, 2],
        'unit_price': [25.99, 149.99, 15.99, 25.99, 89.99],
        'discount_rate': [0.1, 0.0, 0.15, 0.05, 0.0]
    }

    # Customer information
    customer_data = {
        'customer_id': [201, 202, 203],
        'customer_tier': ['Gold', 'Silver', 'Bronze'],
        'region': ['North', 'South', 'East'],
        'lifetime_value': [1500.0, 800.0, 300.0]
    }

    # Product catalog
    product_data = {
        'product_id': ['P001', 'P002', 'P003', 'P004'],
        'category': ['Electronics', 'Computers', 'Accessories', 'Electronics'],
        'cost_price': [15.00, 100.00, 8.00, 60.00],
        'supplier': ['SupplierA', 'SupplierB', 'SupplierA', 'SupplierC']
    }

    # Create LineageDataFrames with metadata
    sales_df = LineageDataFrame(sales_data, name="sales_transactions",
                                source_type="database", source_location="sales.transactions")
    customers_df = LineageDataFrame(customer_data, name="customer_master",
                                    source_type="database", source_location="crm.customers")
    products_df = LineageDataFrame(product_data, name="product_catalog",
                                   source_type="database", source_location="inventory.products")

    print(f"   Sales transactions: {sales_df.shape}")
    print(f"   Customer data: {customers_df.shape}")
    print(f"   Product catalog: {products_df.shape}")

    # 2. Complex data transformation pipeline
    print("\n2. ⚙️ Complex Data Transformation Pipeline")
    print("-" * 42)

    # Step 1: Calculate financial metrics
    sales_financial = sales_df.assign(
        gross_revenue=lambda x: x['quantity'] * x['unit_price'],
        discount_amount=lambda x: x['gross_revenue'] * x['discount_rate'],
        net_revenue=lambda x: x['gross_revenue'] - x['discount_amount']
    )
    print(f"   ✅ Financial calculations: {sales_financial.shape}")

    # Step 2: Enrich with customer data
    enriched_sales = sales_financial.merge(
        customers_df, on='customer_id', how='left'
    )
    print(f"   ✅ Customer enrichment: {enriched_sales.shape}")

    # Step 3: Add product information
    complete_sales = enriched_sales.merge(
        products_df, on='product_id', how='left'
    )
    print(f"   ✅ Product enrichment: {complete_sales.shape}")

    # Step 4: Calculate profitability
    profitable_sales = complete_sales.assign(
        cost_total=lambda x: x['quantity'] * x['cost_price'],
        profit=lambda x: x['net_revenue'] - x['cost_total'],
        profit_margin=lambda x: (x['profit'] / x['net_revenue'] * 100).round(2)
    )
    print(f"   ✅ Profitability analysis: {profitable_sales.shape}")

    # Step 5: Customer analytics
    customer_summary = profitable_sales.groupby(['customer_id', 'customer_tier']).agg({
        'net_revenue': ['sum', 'mean', 'count'],
        'profit': 'sum',
        'quantity': 'sum'
    }).reset_index()
    print(f"   ✅ Customer analytics: {customer_summary.shape}")

    # Step 6: Product performance
    product_performance = profitable_sales.groupby(['category', 'supplier']).agg({
        'net_revenue': 'sum',
        'profit': 'sum',
        'quantity': 'sum'
    }).reset_index()

    product_performance = product_performance.assign(
        avg_profit_per_unit=lambda x: x['profit'] / x['quantity']
    )
    print(f"   ✅ Product performance: {product_performance.shape}")

    # Step 7: Regional pivot analysis
    regional_pivot = profitable_sales.pivot_table(
        values=['net_revenue', 'profit'],
        index='region',
        columns='category',
        aggfunc='sum',
        fill_value=0
    )
    print(f"   ✅ Regional pivot: {regional_pivot.shape}")

    # 3. Comprehensive lineage analysis
    print("\n3. 🔍 Comprehensive Lineage Analysis")
    print("-" * 37)

    # Initialize all visualizers
    graph_viz = LineageGraphVisualizer()
    column_viz = ColumnLineageVisualizer()
    report_gen = LineageReportGenerator()

    # Graph-level statistics
    summary = graph_viz.get_lineage_summary()
    print(f"   📈 Graph Statistics:")
    print(f"      Total nodes: {summary['total_nodes']}")
    print(f"      Total transformations: {summary['total_edges']}")
    print(f"      Graph density: {summary['graph_density']:.4f}")
    print(f"      Is DAG: {summary['is_dag']}")
    print(f"      Connected components: {summary['connected_components']}")

    # Node breakdown
    print(f"\n   🏗️ Node Types:")
    for node_type, count in summary['node_types'].items():
        print(f"      {node_type.title()}: {count}")

    # Transformation breakdown
    print(f"\n   🔄 Transformation Types:")
    for trans_type, count in summary['transformation_types'].items():
        print(f"      {trans_type}: {count}")

    # 4. Column-level impact analysis
    print("\n4. 📊 Column-Level Impact Analysis")
    print("-" * 35)

    # Analyze key business metrics
    key_metrics = ['net_revenue', 'profit', 'profit_margin']

    for metric in key_metrics:
        impact = column_viz.get_column_impact_analysis(metric)
        print(f"\n   💰 {metric} Impact:")
        print(f"      Downstream columns: {len(impact['downstream_columns'])}")
        print(f"      Affected tables: {len(impact['affected_tables'])}")
        print(f"      Impact score: {impact['impact_score']}")

        if impact['downstream_columns']:
            deps = ', '.join(impact['downstream_columns'][:3])
            if len(impact['downstream_columns']) > 3:
                deps += f" (+{len(impact['downstream_columns']) - 3} more)"
            print(f"      Key dependencies: {deps}")

    # 5. Advanced lineage queries
    print("\n5. 🔎 Advanced Lineage Queries")
    print("-" * 31)

    # Find paths between nodes
    tracker = LineageTracker.get_global_instance()
    source_nodes = [node_id for node_id, node in tracker.nodes.items()
                    if getattr(node, 'source_type', '') == 'database']

    if len(source_nodes) >= 2:
        path = graph_viz.find_path_between_nodes(
            source_nodes[0], source_nodes[1])
        if path:
            print(f"   🛤️  Found transformation path: {len(path)} steps")
        else:
            print(f"   🛤️  No direct path between source tables")

    # Dependency analysis
    if source_nodes:
        sample_node = source_nodes[0]
        upstream = graph_viz.get_upstream_dependencies(sample_node)
        downstream = graph_viz.get_downstream_dependencies(sample_node)

        print(f"   ⬆️  Upstream dependencies: {len(upstream)}")
        print(f"   ⬇️  Downstream dependencies: {len(downstream)}")

    # 6. Generate comprehensive reports
    print("\n6. 📋 Comprehensive Reporting")
    print("-" * 29)

    # Summary report
    full_report = report_gen.generate_summary_report()
    print(f"   📊 Summary Report Generated:")
    print(
        f"      Quality score: {full_report['quality_metrics']['completeness_score']:.1%}")
    print(
        f"      Context coverage: {full_report['quality_metrics']['context_coverage']:.1%}")
    print(
        f"      Column mapping coverage: {full_report['quality_metrics']['column_mapping_coverage']:.1%}")

    # Column-specific reports
    for metric in ['profit', 'net_revenue']:
        col_report = report_gen.generate_column_report(metric)
        deps = col_report['lineage']['total_dependencies']
        print(f"   📈 {metric} report: {deps} dependencies tracked")

    # 7. Multi-format exports
    print("\n7. 📤 Multi-Format Export Capabilities")
    print("-" * 37)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # JSON export (complete lineage data)
        json_exporter = JSONExporter()
        json_file = json_exporter.export(
            str(temp_path / "ecommerce_lineage.json"))

        # HTML report (interactive dashboard)
        html_exporter = HTMLExporter()
        html_file = html_exporter.export(
            str(temp_path / "ecommerce_dashboard.html"))

        # CSV exports (for analysis tools)
        csv_exporter = CSVExporter()
        nodes_csv = csv_exporter.export_nodes(str(temp_path / "nodes.csv"))
        edges_csv = csv_exporter.export_edges(str(temp_path / "edges.csv"))

        # Markdown summary (for documentation)
        md_exporter = MarkdownExporter()
        md_file = md_exporter.export(str(temp_path / "lineage_summary.md"))

        print(f"   📄 Generated Files:")
        print(f"      JSON (complete data): {Path(json_file).name}")
        print(f"      HTML (dashboard): {Path(html_file).name}")
        print(
            f"      CSV (nodes/edges): {Path(nodes_csv).name}, {Path(edges_csv).name}")
        print(f"      Markdown (docs): {Path(md_file).name}")
        print(f"   📁 Temporary location: {temp_dir}")

    # 8. Visualization capabilities
    print("\n8. 🎨 Visualization Capabilities")
    print("-" * 32)

    print("   🖼️  Available Visualizations:")
    print("      • Interactive Plotly graphs (web-based)")
    print("      • Static Matplotlib plots (publication-ready)")
    print("      • Graphviz diagrams (professional layouts)")
    print("      • NetworkX analysis (algorithmic insights)")
    print("      • Column dependency maps")
    print("      • Impact analysis charts")

    # Test visualization creation
    try:
        # Create Plotly visualization (don't show in terminal)
        fig = graph_viz.visualize_with_plotly(
            include_columns=False,
            show_plot=False,
            save_html=None
        )
        if fig:
            print("   ✅ Plotly visualization: Ready")
        else:
            print("   ⚠️  Plotly: Not available")
    except Exception as e:
        print(f"   ⚠️  Plotly error: {str(e)[:30]}...")

    # 9. Performance insights
    print("\n9. ⚡ Performance & Scalability")
    print("-" * 31)

    print(f"   📊 Current Pipeline Metrics:")
    print(f"      Nodes tracked: {summary['total_nodes']}")
    print(f"      Transformations: {summary['total_edges']}")
    print(f"      Memory overhead: Minimal (metadata only)")
    print(f"      Thread safety: ✅ Enabled")

    complexity = "Low" if summary['graph_density'] < 0.1 else "Medium" if summary['graph_density'] < 0.3 else "High"
    print(f"      Graph complexity: {complexity}")
    print(
        f"      DAG validation: {'✅ Valid' if summary['is_dag'] else '❌ Cycles detected'}")

    # 10. Production recommendations
    print("\n10. 🚀 Production Integration Guide")
    print("-" * 35)

    print("   🔧 Recommended Setup:")
    print(
        "      • Install visualization extras: pip install 'datalineagepy[visualization]'")
    print("      • Configure selective tracking for large datasets")
    print("      • Set up automated report generation")
    print("      • Integrate with CI/CD pipelines")
    print("      • Monitor lineage quality metrics")

    print("\n   📈 Scaling Strategies:")
    print("      • Use column-level filtering for complex schemas")
    print("      • Export to external visualization tools")
    print("      • Implement lineage caching for repeated analysis")
    print("      • Set up lineage validation in data pipelines")

    print("\n   🎯 Use Cases:")
    print("      • Data governance and compliance")
    print("      • Impact analysis for schema changes")
    print("      • Root cause analysis for data quality issues")
    print("      • Documentation generation")
    print("      • Stakeholder communication")

    print("\n✅ Phase 4 Comprehensive Demo Completed!")
    print("\n🎉 Key Achievements:")
    print("   • Full-featured graph visualization and analysis")
    print("   • Advanced column-level impact tracking")
    print("   • Multi-format reporting and export system")
    print("   • Production-ready visualization tools")
    print("   • Comprehensive lineage query capabilities")
    print("   • Quality metrics and validation framework")

    print(f"\n📊 Final Statistics:")
    print(
        f"   • {summary['total_nodes']} nodes tracked across {len(summary['node_types'])} types")
    print(
        f"   • {summary['total_edges']} transformations across {len(summary['transformation_types'])} types")
    print(f"   • {summary['connected_components']} connected component(s)")
    print(f"   • Graph density: {summary['graph_density']:.4f}")


if __name__ == "__main__":
    main()

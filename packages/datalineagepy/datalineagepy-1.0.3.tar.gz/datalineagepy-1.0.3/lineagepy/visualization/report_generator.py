"""
Report generation for data lineage analysis.
"""

from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import json
from pathlib import Path

from ..core.tracker import LineageTracker
from .graph_visualizer import LineageGraphVisualizer
from .column_visualizer import ColumnLineageVisualizer


class LineageReportGenerator:
    """
    Generate comprehensive reports for data lineage analysis.
    """

    def __init__(self, tracker: Optional[LineageTracker] = None):
        """
        Initialize the report generator.

        Args:
            tracker: LineageTracker instance. If None, uses global instance.
        """
        self.tracker = tracker or LineageTracker.get_global_instance()
        self.graph_visualizer = LineageGraphVisualizer(self.tracker)
        self.column_visualizer = ColumnLineageVisualizer(self.tracker)

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive summary report of the lineage.

        Returns:
            Dictionary containing the summary report
        """
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'generator': 'DataLineagePy',
                'version': '1.0.0'
            },
            'overview': {},
            'nodes': {},
            'transformations': {},
            'data_flow': {},
            'quality_metrics': {}
        }

        # Overview statistics
        stats = self.graph_visualizer.get_lineage_summary()
        report['overview'] = {
            'total_nodes': stats['total_nodes'],
            'total_edges': stats['total_edges'],
            'graph_density': stats['graph_density'],
            'is_dag': stats['is_dag'],
            'connected_components': stats['connected_components']
        }

        # Node analysis
        report['nodes'] = {
            'by_type': stats['node_types'],
            'source_nodes': len(stats['source_nodes']),
            'sink_nodes': len(stats['sink_nodes']),
            'intermediate_nodes': stats['total_nodes'] - len(stats['source_nodes']) - len(stats['sink_nodes'])
        }

        # Transformation analysis
        report['transformations'] = {
            'by_type': stats['transformation_types'],
            'most_common': self._get_most_common_transformations(stats['transformation_types']),
            'complexity_score': self._calculate_complexity_score(stats)
        }

        # Data flow analysis
        report['data_flow'] = self._analyze_data_flow()

        # Quality metrics
        report['quality_metrics'] = self._calculate_quality_metrics()

        return report

    def _get_most_common_transformations(self, transformation_types: Dict[str, int]) -> List[Dict[str, Any]]:
        """Get the most common transformation types."""
        sorted_transformations = sorted(
            transformation_types.items(), key=lambda x: x[1], reverse=True)
        return [{'type': t[0], 'count': t[1]} for t in sorted_transformations[:5]]

    def _calculate_complexity_score(self, stats: Dict[str, Any]) -> float:
        """Calculate a complexity score for the lineage graph."""
        # Simple complexity metric based on nodes, edges, and types
        node_complexity = stats['total_nodes'] * 0.1
        edge_complexity = stats['total_edges'] * 0.2
        type_complexity = len(stats['transformation_types']) * 0.3

        return round(node_complexity + edge_complexity + type_complexity, 2)

    def _analyze_data_flow(self) -> Dict[str, Any]:
        """Analyze data flow patterns in the lineage."""
        G = self.graph_visualizer.create_networkx_graph(include_columns=False)

        # Find longest paths
        longest_paths = []
        try:
            import networkx as nx
            # Find all simple paths and get the longest ones
            source_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
            sink_nodes = [n for n in G.nodes() if G.out_degree(n) == 0]

            max_length = 0
            for source in source_nodes:
                for sink in sink_nodes:
                    try:
                        paths = list(nx.all_simple_paths(G, source, sink))
                        for path in paths:
                            if len(path) > max_length:
                                max_length = len(path)
                                longest_paths = [path]
                            elif len(path) == max_length:
                                longest_paths.append(path)
                    except:
                        continue
        except:
            pass

        return {
            'max_depth': max_length,
            'longest_paths_count': len(longest_paths),
            'avg_node_degree': sum(dict(G.degree()).values()) / len(G.nodes()) if G.nodes() else 0
        }

    def _calculate_quality_metrics(self) -> Dict[str, Any]:
        """Calculate quality metrics for the lineage."""
        total_edges = len(self.tracker.edges)
        edges_with_context = sum(
            1 for edge in self.tracker.edges.values() if edge.code_context)
        edges_with_column_mapping = sum(
            1 for edge in self.tracker.edges.values() if edge.column_mapping)

        return {
            'context_coverage': edges_with_context / total_edges if total_edges > 0 else 0,
            'column_mapping_coverage': edges_with_column_mapping / total_edges if total_edges > 0 else 0,
            'completeness_score': (edges_with_context + edges_with_column_mapping) / (2 * total_edges) if total_edges > 0 else 0
        }

    def generate_column_report(self, column_name: str, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a detailed report for a specific column.

        Args:
            column_name: Name of the column to analyze
            table_name: Optional table name to filter by

        Returns:
            Dictionary containing the column report
        """
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'column_name': column_name,
                'table_name': table_name
            },
            'lineage': {},
            'impact_analysis': {},
            'transformations': [],
            'dependencies': {}
        }

        # Get column lineage
        lineage_graph = self.column_visualizer.create_column_dependency_graph(
            column_name, table_name)

        report['lineage'] = {
            'total_dependencies': len(lineage_graph.nodes()),
            'direct_dependencies': len([n for n in lineage_graph.nodes() if lineage_graph.in_degree(n) == 0]),
            'transformation_depth': self._calculate_transformation_depth(lineage_graph)
        }

        # Impact analysis
        impact_analysis = self.column_visualizer.get_column_impact_analysis(
            column_name, table_name)
        report['impact_analysis'] = impact_analysis

        # Transformation details
        report['transformations'] = self._get_column_transformations(
            column_name, table_name)

        return report

    def _calculate_transformation_depth(self, graph) -> int:
        """Calculate the maximum transformation depth for a column."""
        try:
            import networkx as nx
            if len(graph.nodes()) == 0:
                return 0

            # Find the longest path in the graph
            max_depth = 0
            source_nodes = [
                n for n in graph.nodes() if graph.in_degree(n) == 0]

            for source in source_nodes:
                try:
                    lengths = nx.single_source_shortest_path_length(
                        graph, source)
                    max_depth = max(max_depth, max(
                        lengths.values()) if lengths else 0)
                except:
                    continue

            return max_depth
        except:
            return 0

    def _get_column_transformations(self, column_name: str, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get detailed transformation information for a column."""
        transformations = []

        # Find column nodes
        column_nodes = []
        for node_id, node in self.tracker.nodes.items():
            node_type = node.__class__.__name__.lower().replace('node', '')
            if node_type == 'column' and node.name == column_name:
                if table_name is None or getattr(node, 'table_name', '') == table_name:
                    column_nodes.append(node_id)

        # Find transformations involving these nodes
        for edge_id, edge in self.tracker.edges.items():
            if edge.target_node_id in column_nodes or any(src in column_nodes for src in edge.source_node_ids):
                transformations.append({
                    'operation': edge.operation_name,
                    'type': edge.transformation_type.value,
                    'parameters': edge.parameters,
                    'code_context': edge.code_context,
                    'file_name': edge.file_name,
                    'line_number': edge.line_number,
                    'created_at': edge.created_at.isoformat()
                })

        return transformations

    def generate_html_report(self,
                             output_file: str = "lineage_report.html",
                             include_visualizations: bool = True) -> str:
        """
        Generate an HTML report with embedded visualizations.

        Args:
            output_file: Path to save the HTML report
            include_visualizations: Whether to include interactive visualizations

        Returns:
            Path to the generated HTML file
        """
        summary = self.generate_summary_report()

        html_content = self._create_html_template(
            summary, include_visualizations)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"📊 HTML report generated: {output_file}")
        return output_file

    def _create_html_template(self, summary: Dict[str, Any], include_visualizations: bool) -> str:
        """Create HTML template for the report."""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Lineage Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .metric-label {{ color: #666; font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .quality-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }}
        .quality-fill {{ height: 100%; background: linear-gradient(90deg, #dc3545, #ffc107, #28a745); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Data Lineage Report</h1>
            <p>Generated on {summary['metadata']['generated_at']}</p>
        </div>
        
        <div class="section">
            <h2>📈 Overview</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{summary['overview']['total_nodes']}</div>
                    <div class="metric-label">Total Nodes</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{summary['overview']['total_edges']}</div>
                    <div class="metric-label">Total Transformations</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{summary['overview']['graph_density']:.3f}</div>
                    <div class="metric-label">Graph Density</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{'✅' if summary['overview']['is_dag'] else '❌'}</div>
                    <div class="metric-label">Is DAG</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🔗 Node Analysis</h2>
            <table>
                <tr><th>Node Type</th><th>Count</th></tr>
                {self._create_table_rows(summary['nodes']['by_type'])}
            </table>
        </div>
        
        <div class="section">
            <h2>⚙️ Transformations</h2>
            <table>
                <tr><th>Transformation Type</th><th>Count</th></tr>
                {self._create_table_rows(summary['transformations']['by_type'])}
            </table>
            <p><strong>Complexity Score:</strong> {summary['transformations']['complexity_score']}</p>
        </div>
        
        <div class="section">
            <h2>📊 Quality Metrics</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{summary['quality_metrics']['context_coverage']:.1%}</div>
                    <div class="metric-label">Context Coverage</div>
                    <div class="quality-bar">
                        <div class="quality-fill" style="width: {summary['quality_metrics']['context_coverage']:.1%}"></div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{summary['quality_metrics']['column_mapping_coverage']:.1%}</div>
                    <div class="metric-label">Column Mapping Coverage</div>
                    <div class="quality-bar">
                        <div class="quality-fill" style="width: {summary['quality_metrics']['column_mapping_coverage']:.1%}"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🌊 Data Flow</h2>
            <p><strong>Maximum Depth:</strong> {summary['data_flow']['max_depth']}</p>
            <p><strong>Longest Paths:</strong> {summary['data_flow']['longest_paths_count']}</p>
            <p><strong>Average Node Degree:</strong> {summary['data_flow']['avg_node_degree']:.2f}</p>
        </div>
    </div>
</body>
</html>
        """
        return html

    def _create_table_rows(self, data: Dict[str, int]) -> str:
        """Create HTML table rows from dictionary data."""
        rows = []
        for key, value in data.items():
            rows.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
        return "\n".join(rows)

    def export_to_json(self, output_file: str = "lineage_data.json") -> str:
        """
        Export lineage data to JSON format.

        Args:
            output_file: Path to save the JSON file

        Returns:
            Path to the generated JSON file
        """
        data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'exporter': 'DataLineagePy'
            },
            'nodes': {node_id: node.to_dict() for node_id, node in self.tracker.nodes.items()},
            'edges': {edge_id: edge.to_dict() for edge_id, edge in self.tracker.edges.items()},
            'summary': self.generate_summary_report()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        print(f"📄 JSON export completed: {output_file}")
        return output_file

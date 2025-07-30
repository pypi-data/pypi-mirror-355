"""
Export utilities for different output formats.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

from ..core.tracker import LineageTracker


class BaseExporter:
    """Base class for all exporters."""

    def __init__(self, tracker: Optional[LineageTracker] = None):
        """
        Initialize the exporter.

        Args:
            tracker: LineageTracker instance. If None, uses global instance.
        """
        self.tracker = tracker or LineageTracker.get_global_instance()


class JSONExporter(BaseExporter):
    """Export lineage data to JSON format."""

    def export(self, output_file: str = "lineage_export.json", include_summary: bool = True) -> str:
        """
        Export lineage data to JSON.

        Args:
            output_file: Path to save the JSON file
            include_summary: Whether to include summary statistics

        Returns:
            Path to the generated JSON file
        """
        data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'exporter': 'DataLineagePy JSONExporter',
                'version': '1.0.0'
            },
            'nodes': {},
            'edges': {}
        }

        # Export nodes
        for node_id, node in self.tracker.nodes.items():
            data['nodes'][node_id] = node.to_dict()

        # Export edges
        for edge_id, edge in self.tracker.edges.items():
            data['edges'][edge_id] = edge.to_dict()

        # Add summary if requested
        if include_summary:
            from .graph_visualizer import LineageGraphVisualizer
            visualizer = LineageGraphVisualizer(self.tracker)
            data['summary'] = visualizer.get_lineage_summary()

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        print(f"📄 JSON export completed: {output_file}")
        return output_file


class HTMLExporter(BaseExporter):
    """Export lineage data to HTML format."""

    def export(self,
               output_file: str = "lineage_export.html",
               include_visualizations: bool = True,
               theme: str = "light") -> str:
        """
        Export lineage data to HTML.

        Args:
            output_file: Path to save the HTML file
            include_visualizations: Whether to include interactive visualizations
            theme: Theme for the HTML (light/dark)

        Returns:
            Path to the generated HTML file
        """
        from .report_generator import LineageReportGenerator

        report_gen = LineageReportGenerator(self.tracker)
        return report_gen.generate_html_report(output_file, include_visualizations)


class GraphvizExporter(BaseExporter):
    """Export lineage data to Graphviz DOT format."""

    def export(self,
               output_file: str = "lineage_graph",
               format: str = "png",
               include_columns: bool = True,
               engine: str = "dot") -> Optional[str]:
        """
        Export lineage graph using Graphviz.

        Args:
            output_file: Output file name (without extension)
            format: Output format (png, svg, pdf, etc.)
            include_columns: Whether to include column nodes
            engine: Graphviz layout engine

        Returns:
            Path to generated file or None if Graphviz not available
        """
        if not HAS_GRAPHVIZ:
            print("⚠️  Graphviz not available. Install with: pip install graphviz")
            return None

        from .graph_visualizer import LineageGraphVisualizer

        visualizer = LineageGraphVisualizer(self.tracker)
        return visualizer.visualize_with_graphviz(
            output_file=output_file,
            format=format,
            include_columns=include_columns,
            engine=engine
        )

    def export_dot_source(self, output_file: str = "lineage_graph.dot", include_columns: bool = True) -> str:
        """
        Export raw DOT source code.

        Args:
            output_file: Path to save the DOT file
            include_columns: Whether to include column nodes

        Returns:
            Path to the generated DOT file
        """
        if not HAS_GRAPHVIZ:
            print("⚠️  Graphviz not available. Install with: pip install graphviz")
            return output_file

        from .graph_visualizer import LineageGraphVisualizer

        visualizer = LineageGraphVisualizer(self.tracker)
        G = visualizer.create_networkx_graph(include_columns=include_columns)

        # Create Graphviz graph
        dot = graphviz.Digraph(comment='Data Lineage Graph')
        dot.attr(rankdir='TB', size='12,8', dpi='300')

        # Add nodes
        for node_id, node_data in G.nodes(data=True):
            dot.node(
                node_id,
                label=node_data['label'],
                color=node_data['color'],
                shape=node_data['shape'],
                style='filled',
                fontsize='10'
            )

        # Add edges
        for source, target, edge_data in G.edges(data=True):
            dot.edge(
                source,
                target,
                label=edge_data['label'],
                color=edge_data['color'],
                fontsize='8'
            )

        # Save DOT source
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(dot.source)

        print(f"📄 DOT source exported: {output_file}")
        return output_file


class CSVExporter(BaseExporter):
    """Export lineage data to CSV format."""

    def export_nodes(self, output_file: str = "lineage_nodes.csv") -> str:
        """
        Export nodes to CSV format.

        Args:
            output_file: Path to save the CSV file

        Returns:
            Path to the generated CSV file
        """
        import csv

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if not self.tracker.nodes:
                f.write("No nodes to export\n")
                return output_file

            # Get all possible fields from nodes
            all_fields = set()
            for node in self.tracker.nodes.values():
                node_dict = node.to_dict()
                all_fields.update(node_dict.keys())

            writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
            writer.writeheader()

            for node in self.tracker.nodes.values():
                writer.writerow(node.to_dict())

        print(f"📄 Nodes CSV export completed: {output_file}")
        return output_file

    def export_edges(self, output_file: str = "lineage_edges.csv") -> str:
        """
        Export edges to CSV format.

        Args:
            output_file: Path to save the CSV file

        Returns:
            Path to the generated CSV file
        """
        import csv

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if not self.tracker.edges:
                f.write("No edges to export\n")
                return output_file

            # Get all possible fields from edges
            all_fields = set()
            for edge in self.tracker.edges.values():
                edge_dict = edge.to_dict()
                all_fields.update(edge_dict.keys())

            writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
            writer.writeheader()

            for edge in self.tracker.edges.values():
                edge_dict = edge.to_dict()
                # Convert lists to strings for CSV
                for key, value in edge_dict.items():
                    if isinstance(value, list):
                        edge_dict[key] = '; '.join(map(str, value))
                    elif isinstance(value, dict):
                        edge_dict[key] = json.dumps(value)
                writer.writerow(edge_dict)

        print(f"📄 Edges CSV export completed: {output_file}")
        return output_file


class MarkdownExporter(BaseExporter):
    """Export lineage data to Markdown format."""

    def export(self, output_file: str = "lineage_report.md") -> str:
        """
        Export lineage summary to Markdown format.

        Args:
            output_file: Path to save the Markdown file

        Returns:
            Path to the generated Markdown file
        """
        from .graph_visualizer import LineageGraphVisualizer

        visualizer = LineageGraphVisualizer(self.tracker)
        summary = visualizer.get_lineage_summary()

        markdown_content = f"""# Data Lineage Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

- **Total Nodes**: {summary['total_nodes']}
- **Total Edges**: {summary['total_edges']}
- **Graph Density**: {summary['graph_density']:.3f}
- **Is DAG**: {'Yes' if summary['is_dag'] else 'No'}
- **Connected Components**: {summary['connected_components']}

## Node Types

| Node Type | Count |
|-----------|-------|
"""

        for node_type, count in summary['node_types'].items():
            markdown_content += f"| {node_type} | {count} |\n"

        markdown_content += f"""
## Transformation Types

| Transformation Type | Count |
|-------------------|-------|
"""

        for trans_type, count in summary['transformation_types'].items():
            markdown_content += f"| {trans_type} | {count} |\n"

        markdown_content += f"""
## Graph Structure

- **Source Nodes**: {len(summary['source_nodes'])}
- **Sink Nodes**: {len(summary['sink_nodes'])}
- **Intermediate Nodes**: {summary['total_nodes'] - len(summary['source_nodes']) - len(summary['sink_nodes'])}

## Nodes Details

### Source Nodes
"""

        for node_id in summary['source_nodes'][:10]:  # Limit to first 10
            node = self.tracker.nodes.get(node_id)
            if node:
                markdown_content += f"- `{node.name}` ({node.node_type})\n"

        markdown_content += "\n### Sink Nodes\n"

        for node_id in summary['sink_nodes'][:10]:  # Limit to first 10
            node = self.tracker.nodes.get(node_id)
            if node:
                markdown_content += f"- `{node.name}` ({node.node_type})\n"

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"📄 Markdown export completed: {output_file}")
        return output_file

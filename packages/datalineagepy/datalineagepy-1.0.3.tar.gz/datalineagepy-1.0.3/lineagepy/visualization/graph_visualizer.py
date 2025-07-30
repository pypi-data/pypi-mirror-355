"""
Graph visualization for data lineage using multiple backends.
"""

import networkx as nx
from typing import Dict, Any, Optional, List, Set, Tuple
from enum import Enum
import json
from datetime import datetime

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from ..core.tracker import LineageTracker
from ..core.edges import TransformationType


class VisualizationBackend(Enum):
    """Available visualization backends."""
    GRAPHVIZ = "graphviz"
    PLOTLY = "plotly"
    MATPLOTLIB = "matplotlib"
    NETWORKX = "networkx"


class LineageGraphVisualizer:
    """
    Main class for visualizing data lineage graphs using various backends.
    """

    def __init__(self, tracker: Optional[LineageTracker] = None):
        """
        Initialize the visualizer.

        Args:
            tracker: LineageTracker instance. If None, uses global instance.
        """
        self.tracker = tracker or LineageTracker.get_global_instance()
        self._color_scheme = self._get_default_color_scheme()

    def _get_default_color_scheme(self) -> Dict[str, str]:
        """Get default color scheme for different node and edge types."""
        return {
            # Node colors by type
            'table_node': '#4CAF50',      # Green
            'column_node': '#2196F3',     # Blue
            'intermediate': '#FF9800',    # Orange
            'source': '#9C27B0',          # Purple
            'sink': '#F44336',            # Red

            # Edge colors by transformation type
            'select': '#607D8B',          # Blue Grey
            'filter': '#795548',          # Brown
            'aggregate': '#E91E63',       # Pink
            'merge': '#00BCD4',           # Cyan
            'join': '#00BCD4',            # Cyan
            'assign': '#8BC34A',          # Light Green
            'groupby': '#FF5722',         # Deep Orange
            'concat': '#3F51B5',          # Indigo
            'pivot': '#9E9E9E',           # Grey
            'melt': '#CDDC39',            # Lime
            'apply': '#FFC107',           # Amber
            'default': '#757575'          # Grey
        }

    def create_networkx_graph(self,
                              include_columns: bool = True,
                              filter_nodes: Optional[Set[str]] = None) -> nx.DiGraph:
        """
        Create a NetworkX graph from the lineage data.

        Args:
            include_columns: Whether to include column nodes
            filter_nodes: Set of node IDs to include (None for all)

        Returns:
            NetworkX DiGraph representing the lineage
        """
        G = nx.DiGraph()

        # Add nodes
        for node_id, node in self.tracker.nodes.items():
            if filter_nodes and node_id not in filter_nodes:
                continue

                node_type = node.__class__.__name__.lower().replace('node', '')
                if not include_columns and node_type == 'column':
                    continue

            # Node attributes for visualization
            node_type = node.__class__.__name__.lower().replace('node', '')
            node_attrs = {
                'label': node.name,
                'type': node_type,
                'source_type': getattr(node, 'source_type', 'unknown'),
                'color': self._get_node_color(node),
                'shape': self._get_node_shape(node),
                'size': self._get_node_size(node)
            }

            G.add_node(node_id, **node_attrs)

        # Add edges
        for edge_id, edge in self.tracker.edges.items():
            # Skip edges if nodes are filtered out
            if filter_nodes:
                if edge.target_node_id not in filter_nodes:
                    continue
                if not any(src_id in filter_nodes for src_id in edge.source_node_ids):
                    continue

            # Add edges from each source to target
            for source_id in edge.source_node_ids:
                if source_id in G.nodes and edge.target_node_id in G.nodes:
                    edge_attrs = {
                        'label': edge.operation_name,
                        'transformation_type': edge.transformation_type.value,
                        'color': self._get_edge_color(edge),
                        'weight': self._get_edge_weight(edge),
                        'style': self._get_edge_style(edge),
                        'edge_id': edge_id
                    }

                    G.add_edge(source_id, edge.target_node_id, **edge_attrs)

        return G

    def _get_node_color(self, node) -> str:
        """Get color for a node based on its type."""
        node_type = node.__class__.__name__.lower().replace('node', '')
        source_type = getattr(node, 'source_type', 'unknown')

        if source_type == 'source':
            return self._color_scheme['source']
        elif node_type == 'table':
            return self._color_scheme['table_node']
        elif node_type == 'column':
            return self._color_scheme['column_node']
        else:
            return self._color_scheme['intermediate']

    def _get_node_shape(self, node) -> str:
        """Get shape for a node based on its type."""
        node_type = node.__class__.__name__.lower().replace('node', '')
        if node_type == 'table':
            return 'box'
        elif node_type == 'column':
            return 'ellipse'
        else:
            return 'diamond'

    def _get_node_size(self, node) -> int:
        """Get size for a node based on its importance."""
        # Could be based on number of downstream dependencies
        return 20

    def _get_edge_color(self, edge) -> str:
        """Get color for an edge based on transformation type."""
        trans_type = edge.transformation_type.value
        return self._color_scheme.get(trans_type, self._color_scheme['default'])

    def _get_edge_weight(self, edge) -> float:
        """Get weight for an edge (affects thickness)."""
        # Could be based on data volume or importance
        return 1.0

    def _get_edge_style(self, edge) -> str:
        """Get style for an edge."""
        return 'solid'

    def visualize_with_graphviz(self,
                                output_file: str = "lineage_graph",
                                format: str = "png",
                                include_columns: bool = True,
                                engine: str = "dot") -> Optional[str]:
        """
        Create visualization using Graphviz.

        Args:
            output_file: Output file name (without extension)
            format: Output format (png, svg, pdf, etc.)
            include_columns: Whether to include column nodes
            engine: Graphviz layout engine (dot, neato, fdp, etc.)

        Returns:
            Path to generated file or None if Graphviz not available
        """
        if not HAS_GRAPHVIZ:
            print("⚠️  Graphviz not available. Install with: pip install graphviz")
            return None

        # Create NetworkX graph
        G = self.create_networkx_graph(include_columns=include_columns)

        # Create Graphviz graph
        dot = graphviz.Digraph(comment='Data Lineage Graph', engine=engine)
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

        # Render
        output_path = dot.render(output_file, format=format, cleanup=True)
        print(f"📊 Graphviz visualization saved to: {output_path}")
        return output_path

    def visualize_with_plotly(self,
                              include_columns: bool = True,
                              show_plot: bool = True,
                              save_html: Optional[str] = None) -> Optional[go.Figure]:
        """
        Create interactive visualization using Plotly.

        Args:
            include_columns: Whether to include column nodes
            show_plot: Whether to display the plot
            save_html: Path to save HTML file (optional)

        Returns:
            Plotly Figure object or None if Plotly not available
        """
        if not HAS_PLOTLY:
            print("⚠️  Plotly not available. Install with: pip install plotly")
            return None

        # Create NetworkX graph
        G = self.create_networkx_graph(include_columns=include_columns)

        if len(G.nodes()) == 0:
            print("⚠️  No nodes to visualize")
            return None

        # Calculate layout
        try:
            pos = nx.spring_layout(G, k=3, iterations=50)
        except:
            # Fallback for single node
            pos = {list(G.nodes())[0]: (0, 0)}

        # Extract node information
        node_trace = go.Scatter(
            x=[pos[node][0] for node in G.nodes()],
            y=[pos[node][1] for node in G.nodes()],
            mode='markers+text',
            text=[G.nodes[node]['label'] for node in G.nodes()],
            textposition="middle center",
            marker=dict(
                size=[G.nodes[node]['size'] for node in G.nodes()],
                color=[G.nodes[node]['color'] for node in G.nodes()],
                line=dict(width=2, color='black')
            ),
            hovertemplate='<b>%{text}</b><br>Type: %{customdata}<extra></extra>',
            customdata=[G.nodes[node]['type'] for node in G.nodes()],
            name='Nodes'
        )

        # Extract edge information
        edge_x = []
        edge_y = []
        edge_info = []

        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_info.append(G.edges[edge]['label'])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines',
            name='Edges'
        )

        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
            title='Data Lineage Graph',
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[dict(
                text="Interactive Data Lineage Visualization",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor="left", yanchor="bottom",
                font=dict(color="#888", size=12)
            )],
            xaxis=dict(showgrid=False, zeroline=False,
                       showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False,
                       showticklabels=False)
        ))

        if save_html:
            fig.write_html(save_html)
            print(f"📊 Interactive visualization saved to: {save_html}")

        if show_plot:
            fig.show()

        return fig

    def visualize_with_matplotlib(self,
                                  output_file: Optional[str] = None,
                                  include_columns: bool = True,
                                  figsize: Tuple[int, int] = (12, 8)) -> Optional[plt.Figure]:
        """
        Create visualization using Matplotlib.

        Args:
            output_file: Path to save the figure
            include_columns: Whether to include column nodes
            figsize: Figure size (width, height)

        Returns:
            Matplotlib Figure object or None if matplotlib not available
        """
        if not HAS_MATPLOTLIB:
            print("⚠️  Matplotlib not available. Install with: pip install matplotlib")
            return None

        # Create NetworkX graph
        G = self.create_networkx_graph(include_columns=include_columns)

        if len(G.nodes()) == 0:
            print("⚠️  No nodes to visualize")
            return None

        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Calculate layout
        try:
            pos = nx.spring_layout(G, k=3, iterations=50)
        except:
            pos = {list(G.nodes())[0]: (0, 0)}

        # Draw edges
        nx.draw_networkx_edges(
            G, pos, ax=ax, edge_color='gray', alpha=0.6, arrows=True)

        # Draw nodes by type
        node_types = set(G.nodes[node]['type'] for node in G.nodes())

        for node_type in node_types:
            nodes_of_type = [node for node in G.nodes(
            ) if G.nodes[node]['type'] == node_type]
            colors = [G.nodes[node]['color'] for node in nodes_of_type]

            nx.draw_networkx_nodes(
                G, pos,
                nodelist=nodes_of_type,
                node_color=colors,
                node_size=300,
                alpha=0.8,
                ax=ax
            )

        # Draw labels
        labels = {node: G.nodes[node]['label'] for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax)

        # Add title and formatting
        ax.set_title('Data Lineage Graph', fontsize=16, fontweight='bold')
        ax.axis('off')

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"📊 Matplotlib visualization saved to: {output_file}")

        return fig

    def get_lineage_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the lineage graph.

        Returns:
            Dictionary with graph statistics and summary
        """
        G = self.create_networkx_graph(include_columns=True)

        # Basic graph statistics
        stats = {
            'total_nodes': len(G.nodes()),
            'total_edges': len(G.edges()),
            'node_types': {},
            'transformation_types': {},
            'graph_density': nx.density(G) if len(G.nodes()) > 1 else 0,
            'is_dag': nx.is_directed_acyclic_graph(G),
            'connected_components': nx.number_weakly_connected_components(G)
        }

        # Count node types
        for node in G.nodes():
            node_type = G.nodes[node]['type']
            stats['node_types'][node_type] = stats['node_types'].get(
                node_type, 0) + 1

        # Count transformation types
        for edge in G.edges():
            trans_type = G.edges[edge]['transformation_type']
            stats['transformation_types'][trans_type] = stats['transformation_types'].get(
                trans_type, 0) + 1

        # Find source and sink nodes
        stats['source_nodes'] = [
            node for node in G.nodes() if G.in_degree(node) == 0]
        stats['sink_nodes'] = [
            node for node in G.nodes() if G.out_degree(node) == 0]

        return stats

    def find_path_between_nodes(self, source_node: str, target_node: str) -> Optional[List[str]]:
        """
        Find path between two nodes in the lineage graph.

        Args:
            source_node: Source node ID
            target_node: Target node ID

        Returns:
            List of node IDs representing the path, or None if no path exists
        """
        G = self.create_networkx_graph(include_columns=True)

        try:
            return nx.shortest_path(G, source_node, target_node)
        except nx.NetworkXNoPath:
            return None
        except nx.NodeNotFound:
            return None

    def get_upstream_dependencies(self, node_id: str, max_depth: Optional[int] = None) -> Set[str]:
        """
        Get all upstream dependencies for a node.

        Args:
            node_id: Target node ID
            max_depth: Maximum depth to traverse (None for unlimited)

        Returns:
            Set of upstream node IDs
        """
        G = self.create_networkx_graph(include_columns=True)

        if node_id not in G.nodes():
            return set()

        upstream = set()

        def traverse_upstream(current_node: str, depth: int = 0):
            if max_depth is not None and depth >= max_depth:
                return

            for predecessor in G.predecessors(current_node):
                if predecessor not in upstream:
                    upstream.add(predecessor)
                    traverse_upstream(predecessor, depth + 1)

        traverse_upstream(node_id)
        return upstream

    def get_downstream_dependencies(self, node_id: str, max_depth: Optional[int] = None) -> Set[str]:
        """
        Get all downstream dependencies for a node.

        Args:
            node_id: Source node ID
            max_depth: Maximum depth to traverse (None for unlimited)

        Returns:
            Set of downstream node IDs
        """
        G = self.create_networkx_graph(include_columns=True)

        if node_id not in G.nodes():
            return set()

        downstream = set()

        def traverse_downstream(current_node: str, depth: int = 0):
            if max_depth is not None and depth >= max_depth:
                return

            for successor in G.successors(current_node):
                if successor not in downstream:
                    downstream.add(successor)
                    traverse_downstream(successor, depth + 1)

        traverse_downstream(node_id)
        return downstream

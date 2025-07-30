"""
Column-level lineage visualization.
"""

from typing import Dict, Any, Optional, List, Set
import networkx as nx

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from ..core.tracker import LineageTracker


class ColumnLineageVisualizer:
    """
    Visualizer for column-level data lineage.
    """

    def __init__(self, tracker: Optional[LineageTracker] = None):
        """
        Initialize the column visualizer.

        Args:
            tracker: LineageTracker instance. If None, uses global instance.
        """
        self.tracker = tracker or LineageTracker.get_global_instance()

    def create_column_dependency_graph(self, target_column: str, table_name: Optional[str] = None) -> nx.DiGraph:
        """
        Create a graph showing dependencies for a specific column.

        Args:
            target_column: Name of the target column
            table_name: Optional table name to filter by

        Returns:
            NetworkX DiGraph showing column dependencies
        """
        G = nx.DiGraph()

        # Find all nodes related to the target column
        relevant_nodes = set()

        # Find column nodes matching the target
        for node_id, node in self.tracker.nodes.items():
            node_type = node.__class__.__name__.lower().replace('node', '')
            if node_type == 'column' and node.name == target_column:
                if table_name is None or getattr(node, 'table_name', '') == table_name:
                    relevant_nodes.add(node_id)

        if not relevant_nodes:
            return G

        # Traverse backwards to find all dependencies
        def find_dependencies(node_id: str, visited: Set[str]):
            if node_id in visited:
                return
            visited.add(node_id)

            # Add the node
            if node_id in self.tracker.nodes:
                node = self.tracker.nodes[node_id]
                node_type = node.__class__.__name__.lower().replace('node', '')
                G.add_node(node_id,
                           label=node.name,
                           type=node_type,
                           table=getattr(node, 'table_name', ''))

            # Find edges that target this node
            for edge_id, edge in self.tracker.edges.items():
                if edge.target_node_id == node_id:
                    # Add source nodes
                    for source_id in edge.source_node_ids:
                        if source_id not in visited:
                            find_dependencies(source_id, visited)

                        # Add edge
                        G.add_edge(source_id, node_id,
                                   operation=edge.operation_name,
                                   transformation=edge.transformation_type.value)

        # Start from target columns and work backwards
        visited = set()
        for node_id in relevant_nodes:
            find_dependencies(node_id, visited)

        return G

    def visualize_column_lineage(self,
                                 target_column: str,
                                 table_name: Optional[str] = None,
                                 show_plot: bool = True,
                                 save_html: Optional[str] = None) -> Optional[go.Figure]:
        """
        Create an interactive visualization of column lineage.

        Args:
            target_column: Name of the target column
            table_name: Optional table name to filter by
            show_plot: Whether to display the plot
            save_html: Path to save HTML file (optional)

        Returns:
            Plotly Figure object or None if Plotly not available
        """
        if not HAS_PLOTLY:
            print("⚠️  Plotly not available. Install with: pip install plotly")
            return None

        G = self.create_column_dependency_graph(target_column, table_name)

        if len(G.nodes()) == 0:
            print(f"⚠️  No lineage found for column '{target_column}'")
            return None

        # Calculate layout
        pos = nx.spring_layout(G, k=2, iterations=50)

        # Create node traces by type
        node_traces = []
        node_types = set(G.nodes[node]['type'] for node in G.nodes())

        colors = {'table': '#4CAF50',
                  'column': '#2196F3', 'unknown': '#FF9800'}

        for node_type in node_types:
            nodes_of_type = [node for node in G.nodes(
            ) if G.nodes[node]['type'] == node_type]

            node_trace = go.Scatter(
                x=[pos[node][0] for node in nodes_of_type],
                y=[pos[node][1] for node in nodes_of_type],
                mode='markers+text',
                text=[G.nodes[node]['label'] for node in nodes_of_type],
                textposition="middle center",
                marker=dict(
                    size=30,
                    color=colors.get(node_type, colors['unknown']),
                    line=dict(width=2, color='black')
                ),
                name=f'{node_type.title()} Nodes',
                hovertemplate='<b>%{text}</b><br>Type: ' +
                node_type + '<extra></extra>'
            )
            node_traces.append(node_trace)

        # Create edge trace
        edge_x = []
        edge_y = []
        edge_info = []

        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_info.append(G.edges[edge]['operation'])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines',
            name='Dependencies'
        )

        # Create figure
        fig = go.Figure(data=[edge_trace] + node_traces,
                        layout=go.Layout(
            title=f'Column Lineage: {target_column}',
            titlefont_size=16,
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False,
                       showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False,
                       showticklabels=False)
        ))

        if save_html:
            fig.write_html(save_html)
            print(f"📊 Column lineage visualization saved to: {save_html}")

        if show_plot:
            fig.show()

        return fig

    def get_column_impact_analysis(self, source_column: str, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze the impact of a source column on downstream columns.

        Args:
            source_column: Name of the source column
            table_name: Optional table name to filter by

        Returns:
            Dictionary with impact analysis results
        """
        # Find source column nodes
        source_nodes = []
        for node_id, node in self.tracker.nodes.items():
            node_type = node.__class__.__name__.lower().replace('node', '')
            if node_type == 'column' and node.name == source_column:
                if table_name is None or getattr(node, 'table_name', '') == table_name:
                    source_nodes.append(node_id)

        if not source_nodes:
            return {'error': f'Column {source_column} not found'}

        # Find all downstream columns
        downstream_columns = set()
        downstream_tables = set()
        transformation_paths = []

        def traverse_downstream(node_id: str, path: List[str]):
            current_node = self.tracker.nodes.get(node_id)
            if current_node:
                node_type = current_node.__class__.__name__.lower().replace('node', '')
                if node_type == 'column':
                    downstream_columns.add(current_node.name)
                    if hasattr(current_node, 'table_name'):
                        downstream_tables.add(current_node.table_name)

            # Find edges from this node
            for edge_id, edge in self.tracker.edges.items():
                if node_id in edge.source_node_ids:
                    new_path = path + [edge.operation_name]
                    transformation_paths.append({
                        'target': edge.target_node_id,
                        'path': new_path,
                        'transformation': edge.transformation_type.value
                    })
                    traverse_downstream(edge.target_node_id, new_path)

        # Start traversal from source nodes
        for source_node_id in source_nodes:
            traverse_downstream(source_node_id, [])

        return {
            'source_column': source_column,
            'source_table': table_name,
            'downstream_columns': list(downstream_columns),
            'affected_tables': list(downstream_tables),
            'transformation_paths': transformation_paths,
            'impact_score': len(downstream_columns)
        }

    def create_column_flow_diagram(self,
                                   columns: List[str],
                                   show_plot: bool = True,
                                   save_html: Optional[str] = None) -> Optional[go.Figure]:
        """
        Create a flow diagram showing how multiple columns are related.

        Args:
            columns: List of column names to include
            show_plot: Whether to display the plot
            save_html: Path to save HTML file (optional)

        Returns:
            Plotly Figure object or None if Plotly not available
        """
        if not HAS_PLOTLY:
            print("⚠️  Plotly not available. Install with: pip install plotly")
            return None

        # Create a combined graph for all columns
        G = nx.DiGraph()

        for column in columns:
            column_graph = self.create_column_dependency_graph(column)
            G = nx.compose(G, column_graph)

        if len(G.nodes()) == 0:
            print("⚠️  No lineage found for specified columns")
            return None

        # Use hierarchical layout
        pos = nx.spring_layout(G, k=3, iterations=100)

        # Create visualization similar to column lineage but for multiple columns
        node_traces = []
        node_types = set(G.nodes[node]['type'] for node in G.nodes())

        colors = {'table': '#4CAF50',
                  'column': '#2196F3', 'unknown': '#FF9800'}

        for node_type in node_types:
            nodes_of_type = [node for node in G.nodes(
            ) if G.nodes[node]['type'] == node_type]

            node_trace = go.Scatter(
                x=[pos[node][0] for node in nodes_of_type],
                y=[pos[node][1] for node in nodes_of_type],
                mode='markers+text',
                text=[G.nodes[node]['label'] for node in nodes_of_type],
                textposition="middle center",
                marker=dict(
                    size=25,
                    color=colors.get(node_type, colors['unknown']),
                    line=dict(width=2, color='black')
                ),
                name=f'{node_type.title()} Nodes',
                hovertemplate='<b>%{text}</b><br>Type: ' +
                node_type + '<extra></extra>'
            )
            node_traces.append(node_trace)

        # Create edge trace
        edge_x = []
        edge_y = []

        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines',
            name='Data Flow'
        )

        # Create figure
        fig = go.Figure(data=[edge_trace] + node_traces,
                        layout=go.Layout(
            title=f'Column Flow Diagram: {", ".join(columns)}',
            titlefont_size=16,
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False,
                       showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False,
                       showticklabels=False)
        ))

        if save_html:
            fig.write_html(save_html)
            print(f"📊 Column flow diagram saved to: {save_html}")

        if show_plot:
            fig.show()

        return fig

"""
DataLineagePy dbt Integration

Native dbt integration providing:
- dbt Macros: Native dbt macros for lineage tracking
- Model Dependency: Automatic model-to-model lineage
- Source Lineage: Track dbt sources and seeds
- Test Integration: Data quality test lineage
- Documentation Sync: Sync with dbt documentation
- Manifest Integration: Parse dbt manifest.json for complete lineage
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Set, Union
from pathlib import Path
import re

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from ..core.base_tracker import BaseDataLineageTracker
from ..core.data_node import DataNode

logger = logging.getLogger(__name__)


class DbtManifestParser:
    """
    Parser for dbt manifest.json files to extract model dependencies.
    """

    def __init__(self, manifest_path: Optional[str] = None):
        self.manifest_path = manifest_path
        self.manifest_data: Optional[Dict[str, Any]] = None
        self._load_manifest()

    def _load_manifest(self) -> None:
        """Load dbt manifest.json file."""
        if not self.manifest_path:
            # Try to find manifest in common locations
            common_paths = [
                "./target/manifest.json",
                "./dbt_project/target/manifest.json",
                "../target/manifest.json"
            ]

            for path in common_paths:
                if os.path.exists(path):
                    self.manifest_path = path
                    break

        if self.manifest_path and os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, 'r') as f:
                    self.manifest_data = json.load(f)
                logger.info(f"Loaded dbt manifest from {self.manifest_path}")
            except Exception as e:
                logger.error(f"Failed to load manifest: {e}")
                self.manifest_data = None
        else:
            logger.warning("dbt manifest.json not found")

    def get_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all models from manifest."""
        if not self.manifest_data:
            return {}

        models = {}
        for node_id, node_data in self.manifest_data.get('nodes', {}).items():
            if node_data.get('resource_type') == 'model':
                model_name = node_data.get('name', node_id)
                models[model_name] = {
                    'unique_id': node_id,
                    'name': model_name,
                    'schema': node_data.get('schema'),
                    'database': node_data.get('database'),
                    'depends_on': node_data.get('depends_on', {}),
                    'refs': node_data.get('refs', []),
                    'sources': node_data.get('sources', []),
                    'config': node_data.get('config', {}),
                    'tags': node_data.get('tags', []),
                    'description': node_data.get('description', ''),
                    'columns': node_data.get('columns', {})
                }

        return models

    def get_sources(self) -> Dict[str, Dict[str, Any]]:
        """Get all sources from manifest."""
        if not self.manifest_data:
            return {}

        sources = {}
        for source_id, source_data in self.manifest_data.get('sources', {}).items():
            source_name = source_data.get('name', source_id)
            sources[source_name] = {
                'unique_id': source_id,
                'name': source_name,
                'source_name': source_data.get('source_name'),
                'schema': source_data.get('schema'),
                'database': source_data.get('database'),
                'identifier': source_data.get('identifier'),
                'description': source_data.get('description', ''),
                'columns': source_data.get('columns', {}),
                'loaded_at_field': source_data.get('loaded_at_field'),
                'freshness': source_data.get('freshness', {})
            }

        return sources

    def get_model_dependencies(self, model_name: str) -> Dict[str, List[str]]:
        """Get dependencies for a specific model."""
        models = self.get_models()

        if model_name not in models:
            return {'models': [], 'sources': [], 'seeds': []}

        model_data = models[model_name]
        depends_on = model_data.get('depends_on', {})

        return {
            'models': [dep.split('.')[-1] for dep in depends_on.get('nodes', [])
                       if 'model.' in dep],
            'sources': [f"{src[0]}.{src[1]}" for src in model_data.get('sources', [])],
            'seeds': [dep.split('.')[-1] for dep in depends_on.get('nodes', [])
                      if 'seed.' in dep]
        }

    def get_downstream_models(self, model_name: str) -> List[str]:
        """Get models that depend on the given model."""
        models = self.get_models()
        downstream = []

        for name, model_data in models.items():
            if name != model_name:
                deps = self.get_model_dependencies(name)
                if model_name in deps['models']:
                    downstream.append(name)

        return downstream


class DbtLineageTracker(BaseDataLineageTracker):
    """
    dbt Lineage Tracker

    Tracks lineage for dbt models, sources, tests, and transformations.
    """

    def __init__(self, project_dir: str, manifest_path: Optional[str] = None):
        super().__init__()
        self.project_dir = Path(project_dir)
        self.manifest_parser = DbtManifestParser(manifest_path)
        self.model_lineages: Dict[str, Dict[str, Any]] = {}
        self.run_lineages: Dict[str, Dict[str, Any]] = {}
        self.test_lineages: Dict[str, Dict[str, Any]] = {}

        # Load project configuration
        self.project_config = self._load_project_config()

    def _load_project_config(self) -> Dict[str, Any]:
        """Load dbt_project.yml configuration."""
        project_file = self.project_dir / "dbt_project.yml"

        if not YAML_AVAILABLE:
            logger.warning(
                "PyYAML not available, dbt project config not loaded")
            return {}

        if project_file.exists():
            try:
                with open(project_file, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(
                    f"Loaded dbt project config: {config.get('name', 'unknown')}")
                return config
            except Exception as e:
                logger.error(f"Failed to load dbt project config: {e}")

        return {}

    def sync_model_lineage(self) -> Dict[str, str]:
        """Sync lineage for all models in the project."""
        models = self.manifest_parser.get_models()
        sources = self.manifest_parser.get_sources()
        lineage_ids = {}

        # Create source nodes
        for source_name, source_data in sources.items():
            source_node = DataNode(
                node_id=f"dbt_source_{source_name}",
                node_type="dbt_source",
                metadata={
                    'source_name': source_name,
                    'schema': source_data.get('schema'),
                    'database': source_data.get('database'),
                    'identifier': source_data.get('identifier'),
                    'description': source_data.get('description'),
                    'columns': list(source_data.get('columns', {}).keys())
                }
            )
            self.add_node(source_node)

        # Create model nodes and dependencies
        for model_name, model_data in models.items():
            lineage_id = self.track_model_lineage(
                model_name=model_name,
                model_config=model_data
            )
            lineage_ids[model_name] = lineage_id

        logger.info(
            f"Synced lineage for {len(models)} models and {len(sources)} sources")
        return lineage_ids

    def track_model_lineage(self, model_name: str, model_config: Optional[Dict[str, Any]] = None) -> str:
        """Track lineage for a specific dbt model."""
        lineage_id = self._generate_id()

        if not model_config:
            models = self.manifest_parser.get_models()
            model_config = models.get(model_name, {})

        # Get model dependencies
        dependencies = self.manifest_parser.get_model_dependencies(model_name)

        model_info = {
            'model_name': model_name,
            'dependencies': dependencies,
            'config': model_config,
            'tracked_at': datetime.now(),
            'lineage_id': lineage_id
        }

        self.model_lineages[lineage_id] = model_info

        # Create model node
        model_node = DataNode(
            node_id=f"dbt_model_{model_name}",
            node_type="dbt_model",
            metadata={
                'model_name': model_name,
                'schema': model_config.get('schema'),
                'database': model_config.get('database'),
                'materialization': model_config.get('config', {}).get('materialized', 'view'),
                'tags': model_config.get('tags', []),
                'description': model_config.get('description', ''),
                'columns': list(model_config.get('columns', {}).keys()),
                'lineage_id': lineage_id
            }
        )

        self.add_node(model_node)

        # Add dependencies
        self._add_model_dependencies(model_name, dependencies)

        logger.info(f"Tracked model lineage: {model_name}")
        return lineage_id

    def track_dbt_run(self, command: str, target: str = "dev", models: Optional[List[str]] = None) -> str:
        """Track a dbt run with lineage information."""
        lineage_id = self._generate_id()

        run_info = {
            'command': command,
            'target': target,
            'models': models or [],
            'start_time': datetime.now(),
            'status': 'running',
            'lineage_id': lineage_id
        }

        self.run_lineages[lineage_id] = run_info

        # Create run node
        run_node = DataNode(
            node_id=f"dbt_run_{lineage_id}",
            node_type="dbt_run",
            metadata={
                'command': command,
                'target': target,
                'models': models or [],
                'start_time': str(run_info['start_time']),
                'lineage_id': lineage_id
            }
        )

        self.add_node(run_node)

        # Link run to models
        if models:
            for model_name in models:
                model_node_id = f"dbt_model_{model_name}"
                if model_node_id in [node.node_id for node in self.nodes.values()]:
                    self.add_edge(
                        run_node.node_id,
                        model_node_id,
                        edge_type="runs_model",
                        metadata={'command': command, 'target': target}
                    )

        logger.info(f"Tracking dbt run: {command}")
        return lineage_id

    def complete_dbt_run(self, lineage_id: str, status: str = "success",
                         results: Optional[Dict[str, Any]] = None) -> None:
        """Complete a dbt run tracking."""
        if lineage_id in self.run_lineages:
            self.run_lineages[lineage_id]['end_time'] = datetime.now()
            self.run_lineages[lineage_id]['status'] = status
            self.run_lineages[lineage_id]['results'] = results or {}

            duration = (self.run_lineages[lineage_id]['end_time'] -
                        self.run_lineages[lineage_id]['start_time'])
            self.run_lineages[lineage_id]['duration'] = str(duration)

            logger.info(f"Completed dbt run {lineage_id}: {status}")

    def track_dbt_test(self, test_name: str, model_name: str, test_type: str = "data_test") -> str:
        """Track dbt test execution with lineage."""
        lineage_id = self._generate_id()

        test_info = {
            'test_name': test_name,
            'model_name': model_name,
            'test_type': test_type,
            'timestamp': datetime.now(),
            'status': 'pending',
            'lineage_id': lineage_id
        }

        self.test_lineages[lineage_id] = test_info

        # Create test node
        test_node = DataNode(
            node_id=f"dbt_test_{test_name}_{model_name}",
            node_type="dbt_test",
            metadata={
                'test_name': test_name,
                'model_name': model_name,
                'test_type': test_type,
                'lineage_id': lineage_id
            }
        )

        self.add_node(test_node)

        # Link test to model
        model_node_id = f"dbt_model_{model_name}"
        if model_node_id in [node.node_id for node in self.nodes.values()]:
            self.add_edge(
                model_node_id,
                test_node.node_id,
                edge_type="has_test",
                metadata={'test_type': test_type}
            )

        logger.debug(f"Tracking dbt test: {test_name} for {model_name}")
        return lineage_id

    def analyze_model_impact(self, model_name: str) -> Dict[str, Any]:
        """Analyze the impact of changes to a model."""
        # Get direct dependencies
        dependencies = self.manifest_parser.get_model_dependencies(model_name)

        # Get downstream models
        downstream_models = self.manifest_parser.get_downstream_models(
            model_name)

        # Calculate impact scope
        def get_all_downstream(model: str, visited: Set[str] = None) -> Set[str]:
            if visited is None:
                visited = set()
            if model in visited:
                return visited

            visited.add(model)
            direct_downstream = self.manifest_parser.get_downstream_models(
                model)

            for downstream in direct_downstream:
                get_all_downstream(downstream, visited)

            return visited

        all_downstream = get_all_downstream(model_name)
        all_downstream.discard(model_name)  # Remove self

        # Analyze test impact
        affected_tests = []
        for lineage_id, test_info in self.test_lineages.items():
            if test_info['model_name'] in all_downstream or test_info['model_name'] == model_name:
                affected_tests.append(test_info['test_name'])

        return {
            'model_name': model_name,
            'direct_dependencies': dependencies,
            'direct_downstream': downstream_models,
            'all_downstream': list(all_downstream),
            'impact_scope': len(all_downstream),
            'affected_tests': affected_tests,
            'recommendations': self._get_impact_recommendations(model_name, all_downstream)
        }

    def generate_dbt_docs_lineage(self) -> Dict[str, Any]:
        """Generate lineage information for dbt docs integration."""
        models = self.manifest_parser.get_models()
        sources = self.manifest_parser.get_sources()

        docs_lineage = {
            'models': {},
            'sources': {},
            'lineage_graph': {
                'nodes': [],
                'edges': []
            }
        }

        # Add models to docs
        for model_name, model_data in models.items():
            docs_lineage['models'][model_name] = {
                'name': model_name,
                'description': model_data.get('description', ''),
                'columns': model_data.get('columns', {}),
                'materialization': model_data.get('config', {}).get('materialized', 'view'),
                'tags': model_data.get('tags', [])
            }

            # Add to graph
            docs_lineage['lineage_graph']['nodes'].append({
                'id': f"model.{model_name}",
                'type': 'model',
                'name': model_name
            })

        # Add sources to docs
        for source_name, source_data in sources.items():
            docs_lineage['sources'][source_name] = {
                'name': source_name,
                'description': source_data.get('description', ''),
                'columns': source_data.get('columns', {}),
                'schema': source_data.get('schema'),
                'database': source_data.get('database')
            }

            # Add to graph
            docs_lineage['lineage_graph']['nodes'].append({
                'id': f"source.{source_name}",
                'type': 'source',
                'name': source_name
            })

        # Add edges for dependencies
        for model_name in models.keys():
            dependencies = self.manifest_parser.get_model_dependencies(
                model_name)

            # Model dependencies
            for dep_model in dependencies['models']:
                docs_lineage['lineage_graph']['edges'].append({
                    'source': f"model.{dep_model}",
                    'target': f"model.{model_name}",
                    'type': 'model_dependency'
                })

            # Source dependencies
            for source in dependencies['sources']:
                docs_lineage['lineage_graph']['edges'].append({
                    'source': f"source.{source}",
                    'target': f"model.{model_name}",
                    'type': 'source_dependency'
                })

        return docs_lineage

    def _add_model_dependencies(self, model_name: str, dependencies: Dict[str, List[str]]) -> None:
        """Add model dependencies as lineage edges."""
        model_node_id = f"dbt_model_{model_name}"

        # Add model dependencies
        for dep_model in dependencies['models']:
            dep_node_id = f"dbt_model_{dep_model}"
            self.add_edge(
                dep_node_id,
                model_node_id,
                edge_type="model_dependency",
                metadata={'dependency_type': 'model'}
            )

        # Add source dependencies
        for source in dependencies['sources']:
            source_node_id = f"dbt_source_{source}"
            self.add_edge(
                source_node_id,
                model_node_id,
                edge_type="source_dependency",
                metadata={'dependency_type': 'source'}
            )

        # Add seed dependencies
        for seed in dependencies['seeds']:
            seed_node_id = f"dbt_seed_{seed}"
            self.add_edge(
                seed_node_id,
                model_node_id,
                edge_type="seed_dependency",
                metadata={'dependency_type': 'seed'}
            )

    def _get_impact_recommendations(self, model_name: str, downstream_models: Set[str]) -> List[str]:
        """Get recommendations for model changes."""
        recommendations = []

        if len(downstream_models) == 0:
            recommendations.append(
                "This model has no downstream dependencies - safe to modify")
        elif len(downstream_models) <= 3:
            recommendations.append(
                "Low impact change - test downstream models after modification")
        elif len(downstream_models) <= 10:
            recommendations.append(
                "Medium impact change - consider incremental rollout")
        else:
            recommendations.append(
                "High impact change - requires careful planning and testing")

        if len(downstream_models) > 5:
            recommendations.append(
                "Consider using dbt's state selection for testing")

        recommendations.append(
            f"Run tests for all {len(downstream_models)} downstream models")

        return recommendations


def dbt_lineage_macro() -> str:
    """
    Generate dbt macro for lineage tracking.

    Returns the macro code that can be added to dbt projects.
    """
    macro_code = """
{% macro lineage_track_model() %}
    {{ log("DataLineagePy: Starting lineage tracking for " ~ this, info=true) }}
    {% set lineage_info = {
        'model': this,
        'dependencies': graph.nodes[model.unique_id].depends_on.nodes,
        'timestamp': modules.datetime.datetime.now().isoformat()
    } %}
    {{ log("DataLineagePy lineage: " ~ lineage_info, info=true) }}
{% endmacro %}

{% macro lineage_complete_model() %}
    {{ log("DataLineagePy: Completed lineage tracking for " ~ this, info=true) }}
{% endmacro %}

{% macro lineage_track_test(test_name) %}
    {{ log("DataLineagePy: Tracking test " ~ test_name ~ " for " ~ this, info=true) }}
{% endmacro %}
"""
    return macro_code

"""
DataLineagePy Universal Orchestration Manager

Cross-platform orchestration lineage management providing:
- Multi-Platform Orchestration: Track workflows across different orchestrators
- Workflow Migration: Lineage preservation during platform migrations
- Universal DAG Catalog: Centralized workflow metadata
- Performance Analytics: Cross-platform workflow performance
- Dependency Analysis: Cross-orchestrator dependencies
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.base_tracker import BaseDataLineageTracker
from ..core.data_node import DataNode

logger = logging.getLogger(__name__)


class OrchestrationPlatform(Enum):
    """Supported orchestration platforms."""
    AIRFLOW = "airflow"
    DBT = "dbt"
    PREFECT = "prefect"
    DAGSTER = "dagster"
    AZURE_DATA_FACTORY = "azure_data_factory"
    UNIVERSAL = "universal"


@dataclass
class WorkflowStage:
    """Represents a stage in a cross-platform workflow."""
    stage_id: str
    platform: OrchestrationPlatform
    operation: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None


@dataclass
class CrossPlatformWorkflow:
    """Represents a workflow spanning multiple orchestration platforms."""
    workflow_id: str
    name: str
    description: str
    stages: List[WorkflowStage] = field(default_factory=list)
    platforms: Set[OrchestrationPlatform] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "created"
    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0

    def add_stage(self, stage: WorkflowStage) -> None:
        """Add a stage to the workflow."""
        self.stages.append(stage)
        self.platforms.add(stage.platform)
        self.total_stages += 1

    def get_stages_by_platform(self, platform: OrchestrationPlatform) -> List[WorkflowStage]:
        """Get all stages for a specific platform."""
        return [stage for stage in self.stages if stage.platform == platform]

    def update_stage_status(self, stage_id: str, status: str,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> None:
        """Update the status of a workflow stage."""
        for stage in self.stages:
            if stage.stage_id == stage_id:
                stage.status = status
                if start_time:
                    stage.start_time = start_time
                if end_time:
                    stage.end_time = end_time
                    if stage.start_time:
                        stage.duration = end_time - stage.start_time

                # Update workflow counters
                if status == "completed":
                    self.completed_stages += 1
                elif status == "failed":
                    self.failed_stages += 1
                break


class UniversalOrchestrationManager(BaseDataLineageTracker):
    """
    Universal Orchestration Manager for cross-platform workflow lineage.

    Manages workflows that span multiple orchestration platforms with
    complete lineage tracking and dependency management.
    """

    def __init__(self, platform_trackers: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.platform_trackers = platform_trackers or {}
        self.workflows: Dict[str, CrossPlatformWorkflow] = {}
        self.workflow_catalog: Dict[str, Dict[str, Any]] = {}
        self.cross_platform_dependencies: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

    def register_platform_tracker(self, platform: str, tracker: Any) -> None:
        """Register a platform-specific lineage tracker."""
        self.platform_trackers[platform] = tracker
        logger.info(f"Registered {platform} tracker: {type(tracker).__name__}")

    def create_cross_platform_workflow(self, workflow_id: str, name: str,
                                       description: str = "") -> CrossPlatformWorkflow:
        """Create a new cross-platform workflow."""
        workflow = CrossPlatformWorkflow(
            workflow_id=workflow_id,
            name=name,
            description=description
        )

        self.workflows[workflow_id] = workflow

        # Create workflow node
        workflow_node = DataNode(
            node_id=f"universal_workflow_{workflow_id}",
            node_type="universal_workflow",
            metadata={
                'workflow_id': workflow_id,
                'name': name,
                'description': description,
                'created_at': str(workflow.created_at)
            }
        )

        self.add_node(workflow_node)
        logger.info(f"Created cross-platform workflow: {name} ({workflow_id})")
        return workflow

    def add_airflow_stage(self, workflow_id: str, stage_id: str, dag_id: str,
                          task_id: str, **kwargs) -> WorkflowStage:
        """Add an Airflow stage to a cross-platform workflow."""
        stage = WorkflowStage(
            stage_id=stage_id,
            platform=OrchestrationPlatform.AIRFLOW,
            operation="airflow_task",
            metadata={
                'dag_id': dag_id,
                'task_id': task_id,
                **kwargs
            }
        )

        if workflow_id in self.workflows:
            self.workflows[workflow_id].add_stage(stage)
            self._track_stage_node(workflow_id, stage)

        logger.debug(
            f"Added Airflow stage {stage_id} to workflow {workflow_id}")
        return stage

    def add_dbt_stage(self, workflow_id: str, stage_id: str, project: str,
                      model: str, **kwargs) -> WorkflowStage:
        """Add a dbt stage to a cross-platform workflow."""
        stage = WorkflowStage(
            stage_id=stage_id,
            platform=OrchestrationPlatform.DBT,
            operation="dbt_model",
            metadata={
                'project': project,
                'model': model,
                **kwargs
            }
        )

        if workflow_id in self.workflows:
            self.workflows[workflow_id].add_stage(stage)
            self._track_stage_node(workflow_id, stage)

        logger.debug(f"Added dbt stage {stage_id} to workflow {workflow_id}")
        return stage

    def add_prefect_stage(self, workflow_id: str, stage_id: str, flow_name: str,
                          deployment: str, **kwargs) -> WorkflowStage:
        """Add a Prefect stage to a cross-platform workflow."""
        stage = WorkflowStage(
            stage_id=stage_id,
            platform=OrchestrationPlatform.PREFECT,
            operation="prefect_flow",
            metadata={
                'flow_name': flow_name,
                'deployment': deployment,
                **kwargs
            }
        )

        if workflow_id in self.workflows:
            self.workflows[workflow_id].add_stage(stage)
            self._track_stage_node(workflow_id, stage)

        logger.debug(
            f"Added Prefect stage {stage_id} to workflow {workflow_id}")
        return stage

    def add_dagster_stage(self, workflow_id: str, stage_id: str, asset_name: str,
                          job_name: str, **kwargs) -> WorkflowStage:
        """Add a Dagster stage to a cross-platform workflow."""
        stage = WorkflowStage(
            stage_id=stage_id,
            platform=OrchestrationPlatform.DAGSTER,
            operation="dagster_asset",
            metadata={
                'asset_name': asset_name,
                'job_name': job_name,
                **kwargs
            }
        )

        if workflow_id in self.workflows:
            self.workflows[workflow_id].add_stage(stage)
            self._track_stage_node(workflow_id, stage)

        logger.debug(
            f"Added Dagster stage {stage_id} to workflow {workflow_id}")
        return stage

    def add_stage_dependency(self, workflow_id: str, upstream_stage: str,
                             downstream_stage: str, dependency_type: str = "depends_on") -> None:
        """Add dependency between workflow stages."""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return

        workflow = self.workflows[workflow_id]

        # Update stage dependencies
        for stage in workflow.stages:
            if stage.stage_id == downstream_stage:
                stage.dependencies.append(upstream_stage)
                break

        # Track lineage edge
        upstream_node_id = f"universal_stage_{workflow_id}_{upstream_stage}"
        downstream_node_id = f"universal_stage_{workflow_id}_{downstream_stage}"

        self.add_edge(
            upstream_node_id,
            downstream_node_id,
            edge_type=dependency_type,
            metadata={
                'workflow_id': workflow_id,
                'upstream_stage': upstream_stage,
                'downstream_stage': downstream_stage,
                'dependency_type': dependency_type
            }
        )

        logger.debug(
            f"Added dependency: {upstream_stage} -> {downstream_stage} in {workflow_id}")

    def execute_workflow(self, workflow_id: str, parallel: bool = True) -> Dict[str, Any]:
        """Execute a cross-platform workflow with lineage tracking."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]
        workflow.status = "running"
        execution_start = datetime.now()

        logger.info(
            f"Starting execution of workflow {workflow_id} with {len(workflow.stages)} stages")

        if parallel:
            results = self._execute_workflow_parallel(workflow)
        else:
            results = self._execute_workflow_sequential(workflow)

        execution_end = datetime.now()
        execution_duration = execution_end - execution_start

        # Update workflow status
        if workflow.failed_stages > 0:
            workflow.status = "failed"
        else:
            workflow.status = "completed"

        # Track execution metrics
        execution_results = {
            'workflow_id': workflow_id,
            'status': workflow.status,
            'total_stages': workflow.total_stages,
            'completed_stages': workflow.completed_stages,
            'failed_stages': workflow.failed_stages,
            'execution_duration': str(execution_duration),
            'platforms_used': list(workflow.platforms),
            'stage_results': results
        }

        self.performance_metrics[workflow_id] = execution_results
        logger.info(f"Completed workflow {workflow_id}: {workflow.status}")
        return execution_results

    def _execute_workflow_sequential(self, workflow: CrossPlatformWorkflow) -> List[Dict[str, Any]]:
        """Execute workflow stages sequentially."""
        results = []

        # Build execution order based on dependencies
        execution_order = self._resolve_execution_order(workflow)

        for stage_id in execution_order:
            stage = next(s for s in workflow.stages if s.stage_id == stage_id)
            result = self._execute_stage(workflow.workflow_id, stage)
            results.append(result)

        return results

    def _execute_workflow_parallel(self, workflow: CrossPlatformWorkflow) -> List[Dict[str, Any]]:
        """Execute workflow stages in parallel where possible."""
        results = []

        # Group stages by dependency level
        dependency_levels = self._build_dependency_levels(workflow)

        for level_stages in dependency_levels:
            # Execute all stages in this level in parallel
            futures = []
            for stage_id in level_stages:
                stage = next(
                    s for s in workflow.stages if s.stage_id == stage_id)
                future = self.executor.submit(
                    self._execute_stage, workflow.workflow_id, stage)
                futures.append(future)

            # Wait for all stages in this level to complete
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        return results

    def _execute_stage(self, workflow_id: str, stage: WorkflowStage) -> Dict[str, Any]:
        """Execute a single workflow stage."""
        stage_start = datetime.now()
        stage.start_time = stage_start
        stage.status = "running"

        logger.info(
            f"Executing stage {stage.stage_id} ({stage.platform.value})")

        try:
            # Mock execution based on platform
            if stage.platform == OrchestrationPlatform.AIRFLOW:
                result = self._execute_airflow_stage(stage)
            elif stage.platform == OrchestrationPlatform.DBT:
                result = self._execute_dbt_stage(stage)
            elif stage.platform == OrchestrationPlatform.PREFECT:
                result = self._execute_prefect_stage(stage)
            elif stage.platform == OrchestrationPlatform.DAGSTER:
                result = self._execute_dagster_stage(stage)
            else:
                result = {"status": "completed",
                          "message": f"Mock execution of {stage.platform.value}"}

            stage_end = datetime.now()
            stage.end_time = stage_end
            stage.duration = stage_end - stage_start
            stage.status = "completed"

            # Update workflow counters
            self.workflows[workflow_id].update_stage_status(
                stage.stage_id, "completed", stage_start, stage_end)

            return {
                'stage_id': stage.stage_id,
                'platform': stage.platform.value,
                'status': 'completed',
                'duration': str(stage.duration),
                'result': result
            }

        except Exception as e:
            stage_end = datetime.now()
            stage.end_time = stage_end
            stage.duration = stage_end - stage_start
            stage.status = "failed"

            # Update workflow counters
            self.workflows[workflow_id].update_stage_status(
                stage.stage_id, "failed", stage_start, stage_end)

            logger.error(f"Stage {stage.stage_id} failed: {e}")
            return {
                'stage_id': stage.stage_id,
                'platform': stage.platform.value,
                'status': 'failed',
                'duration': str(stage.duration),
                'error': str(e)
            }

    def _execute_airflow_stage(self, stage: WorkflowStage) -> Dict[str, Any]:
        """Execute an Airflow stage (mock implementation)."""
        dag_id = stage.metadata.get('dag_id', 'unknown')
        task_id = stage.metadata.get('task_id', 'unknown')

        # Simulate Airflow task execution
        logger.info(f"Executing Airflow task {task_id} in DAG {dag_id}")
        return {
            'platform': 'airflow',
            'dag_id': dag_id,
            'task_id': task_id,
            'execution_time': datetime.now().isoformat(),
            'outputs': [f"airflow_output_{task_id}"]
        }

    def _execute_dbt_stage(self, stage: WorkflowStage) -> Dict[str, Any]:
        """Execute a dbt stage (mock implementation)."""
        project = stage.metadata.get('project', 'unknown')
        model = stage.metadata.get('model', 'unknown')

        # Simulate dbt model run
        logger.info(f"Running dbt model {model} in project {project}")
        return {
            'platform': 'dbt',
            'project': project,
            'model': model,
            'execution_time': datetime.now().isoformat(),
            'outputs': [f"dbt_model_{model}"]
        }

    def _execute_prefect_stage(self, stage: WorkflowStage) -> Dict[str, Any]:
        """Execute a Prefect stage (mock implementation)."""
        flow_name = stage.metadata.get('flow_name', 'unknown')
        deployment = stage.metadata.get('deployment', 'unknown')

        # Simulate Prefect flow run
        logger.info(
            f"Running Prefect flow {flow_name} (deployment: {deployment})")
        return {
            'platform': 'prefect',
            'flow_name': flow_name,
            'deployment': deployment,
            'execution_time': datetime.now().isoformat(),
            'outputs': [f"prefect_output_{flow_name}"]
        }

    def _execute_dagster_stage(self, stage: WorkflowStage) -> Dict[str, Any]:
        """Execute a Dagster stage (mock implementation)."""
        asset_name = stage.metadata.get('asset_name', 'unknown')
        job_name = stage.metadata.get('job_name', 'unknown')

        # Simulate Dagster asset materialization
        logger.info(
            f"Materializing Dagster asset {asset_name} in job {job_name}")
        return {
            'platform': 'dagster',
            'asset_name': asset_name,
            'job_name': job_name,
            'execution_time': datetime.now().isoformat(),
            'outputs': [f"dagster_asset_{asset_name}"]
        }

    def analyze_cross_platform_dependencies(self) -> Dict[str, Any]:
        """Analyze dependencies across orchestration platforms."""
        cross_platform_connections = []
        platform_usage = {}

        for workflow in self.workflows.values():
            platforms = list(workflow.platforms)
            platform_usage[workflow.workflow_id] = platforms

            # Find cross-platform dependencies
            for stage in workflow.stages:
                for dep_stage_id in stage.dependencies:
                    dep_stage = next(
                        (s for s in workflow.stages if s.stage_id == dep_stage_id), None)
                    if dep_stage and dep_stage.platform != stage.platform:
                        cross_platform_connections.append({
                            'workflow_id': workflow.workflow_id,
                            'upstream_platform': dep_stage.platform.value,
                            'downstream_platform': stage.platform.value,
                            'upstream_stage': dep_stage_id,
                            'downstream_stage': stage.stage_id
                        })

        return {
            'total_workflows': len(self.workflows),
            'cross_platform_connections': cross_platform_connections,
            'platform_usage': platform_usage,
            'most_used_platforms': self._get_platform_usage_stats(),
            'complexity_score': len(cross_platform_connections)
        }

    def _track_stage_node(self, workflow_id: str, stage: WorkflowStage) -> None:
        """Track a workflow stage as a lineage node."""
        stage_node = DataNode(
            node_id=f"universal_stage_{workflow_id}_{stage.stage_id}",
            node_type="universal_stage",
            metadata={
                'workflow_id': workflow_id,
                'stage_id': stage.stage_id,
                'platform': stage.platform.value,
                'operation': stage.operation,
                'metadata': stage.metadata
            }
        )

        self.add_node(stage_node)

        # Link stage to workflow
        workflow_node_id = f"universal_workflow_{workflow_id}"
        self.add_edge(
            workflow_node_id,
            stage_node.node_id,
            edge_type="contains_stage",
            metadata={'stage_id': stage.stage_id}
        )

    def _resolve_execution_order(self, workflow: CrossPlatformWorkflow) -> List[str]:
        """Resolve execution order based on dependencies."""
        # Simple topological sort implementation
        in_degree = {stage.stage_id: len(stage.dependencies)
                     for stage in workflow.stages}
        queue = [stage_id for stage_id, degree in in_degree.items()
                 if degree == 0]
        execution_order = []

        while queue:
            current = queue.pop(0)
            execution_order.append(current)

            # Find stages that depend on current stage
            for stage in workflow.stages:
                if current in stage.dependencies:
                    in_degree[stage.stage_id] -= 1
                    if in_degree[stage.stage_id] == 0:
                        queue.append(stage.stage_id)

        return execution_order

    def _build_dependency_levels(self, workflow: CrossPlatformWorkflow) -> List[List[str]]:
        """Build dependency levels for parallel execution."""
        levels = []
        remaining_stages = {stage.stage_id: stage for stage in workflow.stages}

        while remaining_stages:
            current_level = []

            # Find stages with no unresolved dependencies
            for stage_id, stage in list(remaining_stages.items()):
                if all(dep not in remaining_stages for dep in stage.dependencies):
                    current_level.append(stage_id)

            # Remove stages in current level
            for stage_id in current_level:
                del remaining_stages[stage_id]

            levels.append(current_level)

        return levels

    def _get_platform_usage_stats(self) -> Dict[str, int]:
        """Get platform usage statistics."""
        platform_counts = {}

        for workflow in self.workflows.values():
            for platform in workflow.platforms:
                platform_counts[platform.value] = platform_counts.get(
                    platform.value, 0) + 1

        return dict(sorted(platform_counts.items(), key=lambda x: x[1], reverse=True))

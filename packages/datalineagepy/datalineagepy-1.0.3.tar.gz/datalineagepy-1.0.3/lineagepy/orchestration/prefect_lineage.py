"""
DataLineagePy Prefect Integration

Native Prefect integration providing:
- Flow Lineage: Automatic Prefect flow lineage tracking
- Task Lineage: Individual task execution lineage
- Deployment Tracking: Prefect deployment and run lineage
- Result Integration: Track Prefect results and artifacts
- Agent Lineage: Track across Prefect agents and work pools
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from functools import wraps

try:
    from prefect import flow, task, Flow, Task
    from prefect.client.orchestration import PrefectClient
    from prefect.deployments import Deployment
    from prefect.infrastructure import Process
    PREFECT_AVAILABLE = True
except ImportError:
    # Mock classes for when Prefect is not available
    def flow(f): return f
    def task(f): return f
    Flow = object
    Task = object
    PrefectClient = object
    Deployment = object
    Process = object
    PREFECT_AVAILABLE = False

from ..core.base_tracker import BaseDataLineageTracker
from ..core.data_node import DataNode

logger = logging.getLogger(__name__)


class PrefectLineageTracker(BaseDataLineageTracker):
    """
    Prefect Lineage Tracker

    Tracks lineage for Prefect flows, tasks, and deployments with native integration.
    """

    def __init__(self, workspace: Optional[str] = None, api_url: Optional[str] = None):
        super().__init__()
        self.workspace = workspace
        self.api_url = api_url
        self.flow_lineages: Dict[str, Dict[str, Any]] = {}
        self.task_lineages: Dict[str, Dict[str, Any]] = {}
        self.deployment_lineages: Dict[str, Dict[str, Any]] = {}
        self.work_pool_lineages: Dict[str, Dict[str, Any]] = {}

    def track_flow_execution(self, flow_name: str, deployment_name: Optional[str] = None,
                             run_id: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Track Prefect flow execution with lineage."""
        lineage_id = self._generate_id()

        flow_info = {
            'flow_name': flow_name,
            'deployment_name': deployment_name,
            'run_id': run_id or f"run_{lineage_id[:8]}",
            'parameters': parameters or {},
            'start_time': datetime.now(),
            'status': 'running',
            'tasks': [],
            'artifacts': [],
            'lineage_id': lineage_id
        }

        self.flow_lineages[lineage_id] = flow_info

        # Create flow node
        flow_node = DataNode(
            node_id=f"prefect_flow_{flow_name}",
            node_type="prefect_flow",
            metadata={
                'flow_name': flow_name,
                'deployment_name': deployment_name,
                'run_id': flow_info['run_id'],
                'parameters': parameters or {},
                'lineage_id': lineage_id
            }
        )

        self.add_node(flow_node)
        logger.info(f"Tracking Prefect flow execution: {flow_name}")
        return lineage_id

    def track_task_execution(self, task_name: str, flow_name: str, run_id: Optional[str] = None,
                             task_inputs: Optional[List[str]] = None,
                             task_outputs: Optional[List[str]] = None) -> str:
        """Track individual task execution within a flow."""
        lineage_id = self._generate_id()

        task_info = {
            'task_name': task_name,
            'flow_name': flow_name,
            'run_id': run_id or f"task_run_{lineage_id[:8]}",
            'task_inputs': task_inputs or [],
            'task_outputs': task_outputs or [],
            'start_time': datetime.now(),
            'status': 'running',
            'lineage_id': lineage_id
        }

        self.task_lineages[lineage_id] = task_info

        # Create task node
        task_node = DataNode(
            node_id=f"prefect_task_{flow_name}_{task_name}",
            node_type="prefect_task",
            metadata={
                'task_name': task_name,
                'flow_name': flow_name,
                'run_id': task_info['run_id'],
                'inputs': task_inputs or [],
                'outputs': task_outputs or [],
                'lineage_id': lineage_id
            }
        )

        self.add_node(task_node)

        # Link task to flow
        flow_node_id = f"prefect_flow_{flow_name}"
        self.add_edge(
            flow_node_id,
            task_node.node_id,
            edge_type="contains_task",
            metadata={'task_name': task_name}
        )

        logger.debug(
            f"Tracking Prefect task execution: {task_name} in {flow_name}")
        return lineage_id

    def complete_flow_run(self, lineage_id: str, status: str = "Completed",
                          final_state: str = "SUCCESS", artifacts: Optional[List[str]] = None) -> None:
        """Complete a flow run tracking."""
        if lineage_id in self.flow_lineages:
            self.flow_lineages[lineage_id]['end_time'] = datetime.now()
            self.flow_lineages[lineage_id]['status'] = status
            self.flow_lineages[lineage_id]['final_state'] = final_state
            self.flow_lineages[lineage_id]['artifacts'] = artifacts or []

            duration = (self.flow_lineages[lineage_id]['end_time'] -
                        self.flow_lineages[lineage_id]['start_time'])
            self.flow_lineages[lineage_id]['duration'] = str(duration)

            logger.info(f"Completed Prefect flow run {lineage_id}: {status}")

    def track_deployment(self, deployment_name: str, flow_name: str,
                         work_pool: Optional[str] = None, schedule: Optional[str] = None) -> str:
        """Track Prefect deployment with lineage."""
        lineage_id = self._generate_id()

        deployment_info = {
            'deployment_name': deployment_name,
            'flow_name': flow_name,
            'work_pool': work_pool,
            'schedule': schedule,
            'created_at': datetime.now(),
            'runs': [],
            'lineage_id': lineage_id
        }

        self.deployment_lineages[lineage_id] = deployment_info

        # Create deployment node
        deployment_node = DataNode(
            node_id=f"prefect_deployment_{deployment_name}",
            node_type="prefect_deployment",
            metadata={
                'deployment_name': deployment_name,
                'flow_name': flow_name,
                'work_pool': work_pool,
                'schedule': schedule,
                'lineage_id': lineage_id
            }
        )

        self.add_node(deployment_node)

        # Link deployment to flow
        flow_node_id = f"prefect_flow_{flow_name}"
        if flow_node_id in [node.node_id for node in self.nodes.values()]:
            self.add_edge(
                deployment_node.node_id,
                flow_node_id,
                edge_type="deploys_flow",
                metadata={'deployment_name': deployment_name}
            )

        logger.info(f"Tracking Prefect deployment: {deployment_name}")
        return lineage_id

    def track_work_pool_execution(self, work_pool_name: str, flow_runs: List[str],
                                  agent_type: str = "process") -> str:
        """Track work pool execution with lineage."""
        lineage_id = self._generate_id()

        work_pool_info = {
            'work_pool_name': work_pool_name,
            'agent_type': agent_type,
            'flow_runs': flow_runs,
            'execution_time': datetime.now(),
            'lineage_id': lineage_id
        }

        self.work_pool_lineages[lineage_id] = work_pool_info

        # Create work pool node
        work_pool_node = DataNode(
            node_id=f"prefect_work_pool_{work_pool_name}",
            node_type="prefect_work_pool",
            metadata={
                'work_pool_name': work_pool_name,
                'agent_type': agent_type,
                'flow_runs': flow_runs,
                'lineage_id': lineage_id
            }
        )

        self.add_node(work_pool_node)
        logger.debug(f"Tracking Prefect work pool: {work_pool_name}")
        return lineage_id

    def track_result_artifacts(self, flow_name: str, run_id: str,
                               artifacts: List[Dict[str, Any]]) -> str:
        """Track Prefect result artifacts with lineage."""
        lineage_id = self._generate_id()

        for artifact in artifacts:
            artifact_node = DataNode(
                node_id=f"prefect_artifact_{artifact.get('name', 'unknown')}_{run_id}",
                node_type="prefect_artifact",
                metadata={
                    'artifact_name': artifact.get('name'),
                    'artifact_type': artifact.get('type'),
                    'flow_name': flow_name,
                    'run_id': run_id,
                    'data': artifact.get('data', {}),
                    'lineage_id': lineage_id
                }
            )

            self.add_node(artifact_node)

            # Link artifact to flow
            flow_node_id = f"prefect_flow_{flow_name}"
            if flow_node_id in [node.node_id for node in self.nodes.values()]:
                self.add_edge(
                    flow_node_id,
                    artifact_node.node_id,
                    edge_type="produces_artifact",
                    metadata={'artifact_name': artifact.get('name')}
                )

        logger.debug(
            f"Tracking {len(artifacts)} Prefect artifacts for {flow_name}")
        return lineage_id

    def analyze_flow_performance(self, flow_name: str) -> Dict[str, Any]:
        """Analyze performance metrics for a flow."""
        flow_runs = [info for info in self.flow_lineages.values()
                     if info['flow_name'] == flow_name]

        if not flow_runs:
            return {'flow_name': flow_name, 'runs': 0}

        successful_runs = [run for run in flow_runs if run.get(
            'final_state') == 'SUCCESS']
        failed_runs = [run for run in flow_runs if run.get(
            'final_state') == 'FAILED']

        # Calculate average duration for completed runs
        completed_runs = [run for run in flow_runs if 'duration' in run]
        avg_duration = None
        if completed_runs:
            durations = [float(run['duration'].split(':')[0]) * 60 +
                         float(run['duration'].split(':')[1]) for run in completed_runs]
            avg_duration = sum(durations) / len(durations)

        return {
            'flow_name': flow_name,
            'total_runs': len(flow_runs),
            'successful_runs': len(successful_runs),
            'failed_runs': len(failed_runs),
            'success_rate': len(successful_runs) / len(flow_runs) * 100 if flow_runs else 0,
            'average_duration_seconds': avg_duration,
            'deployments': list(set(run.get('deployment_name') for run in flow_runs
                                    if run.get('deployment_name')))
        }


def lineage_tracked_flow(func: Callable) -> Callable:
    """
    Decorator for automatic lineage tracking in Prefect flows.

    Usage:
        @lineage_tracked_flow
        @flow
        def my_flow():
            return process_data()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        tracker = PrefectLineageTracker()

        # Get flow information
        flow_name = getattr(func, '__name__', 'unknown_flow')

        # Track flow execution start
        lineage_id = tracker.track_flow_execution(
            flow_name=flow_name,
            parameters=kwargs
        )

        try:
            result = func(*args, **kwargs)

            # Track successful completion
            tracker.complete_flow_run(
                lineage_id=lineage_id,
                status='Completed',
                final_state='SUCCESS'
            )

            logger.info(
                f"Prefect flow {flow_name} completed successfully with lineage {lineage_id}")
            return result

        except Exception as e:
            # Track failed execution
            tracker.complete_flow_run(
                lineage_id=lineage_id,
                status='Failed',
                final_state='FAILED'
            )

            logger.error(f"Prefect flow {flow_name} failed: {e}")
            raise

    return wrapper


def lineage_tracked_task(func: Callable) -> Callable:
    """
    Decorator for automatic lineage tracking in Prefect tasks.

    Usage:
        @lineage_tracked_task
        @task
        def my_task():
            return extract_data()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        tracker = PrefectLineageTracker()

        # Get task information
        task_name = getattr(func, '__name__', 'unknown_task')

        # Try to get flow context (this would be more sophisticated in real implementation)
        flow_name = 'unknown_flow'

        # Track task execution
        lineage_id = tracker.track_task_execution(
            task_name=task_name,
            flow_name=flow_name
        )

        try:
            result = func(*args, **kwargs)

            # Track successful completion
            if lineage_id in tracker.task_lineages:
                tracker.task_lineages[lineage_id]['end_time'] = datetime.now()
                tracker.task_lineages[lineage_id]['status'] = 'completed'
                tracker.task_lineages[lineage_id]['result_type'] = type(
                    result).__name__

            logger.debug(f"Prefect task {task_name} completed successfully")
            return result

        except Exception as e:
            # Track failed execution
            if lineage_id in tracker.task_lineages:
                tracker.task_lineages[lineage_id]['end_time'] = datetime.now()
                tracker.task_lineages[lineage_id]['status'] = 'failed'
                tracker.task_lineages[lineage_id]['error'] = str(e)

            logger.error(f"Prefect task {task_name} failed: {e}")
            raise

    return wrapper


class PrefectLineageClient:
    """
    Enhanced Prefect client with lineage integration.
    """

    def __init__(self, tracker: Optional[PrefectLineageTracker] = None):
        self.tracker = tracker or PrefectLineageTracker()
        if PREFECT_AVAILABLE:
            self.client = PrefectClient()
        else:
            self.client = None

    async def run_deployment(self, deployment_name: str, parameters: Optional[Dict[str, Any]] = None):
        """Run a deployment with lineage tracking."""
        # This would integrate with actual Prefect client in real implementation
        logger.info(
            f"Running deployment {deployment_name} with lineage tracking")

        # Track deployment run
        lineage_id = self.tracker.track_deployment(
            deployment_name=deployment_name,
            flow_name=f"flow_for_{deployment_name}",
            schedule="manual"
        )

        return {
            'deployment_name': deployment_name,
            'lineage_id': lineage_id,
            'status': 'scheduled',
            'parameters': parameters or {}
        }

    async def get_flow_runs(self, flow_name: str) -> List[Dict[str, Any]]:
        """Get flow runs with lineage information."""
        flow_runs = [info for info in self.tracker.flow_lineages.values()
                     if info['flow_name'] == flow_name]

        return [
            {
                'run_id': run['run_id'],
                'status': run['status'],
                'start_time': run['start_time'],
                'parameters': run['parameters'],
                'lineage_id': run['lineage_id']
            }
            for run in flow_runs
        ]

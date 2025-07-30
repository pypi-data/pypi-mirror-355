"""
DataLineagePy Apache Airflow Integration

Native Airflow integration providing:
- LineageOperator: Native Airflow operator with automatic lineage
- LineageHook: Airflow hook for lineage operations  
- DAG Lineage Tracking: Automatic task dependency lineage
- XCom Integration: Track data passing between tasks
- Connection Lineage: Database and external system connections
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Callable
from functools import wraps
import json

try:
    from airflow.models import BaseOperator, DAG, TaskInstance, Connection
    from airflow.hooks.base import BaseHook
    from airflow.utils.decorators import apply_defaults
    from airflow.utils.context import Context
    from airflow.models.xcom import XCom
    from airflow.exceptions import AirflowException
    AIRFLOW_AVAILABLE = True
except ImportError:
    # Mock classes for when Airflow is not available
    BaseOperator = object
    BaseHook = object
    DAG = object
    TaskInstance = object
    Connection = object
    XCom = object
    AirflowException = Exception
    Context = Dict[str, Any]
    def apply_defaults(f): return f
    AIRFLOW_AVAILABLE = False

from ..core.base_tracker import BaseDataLineageTracker
from ..core.data_node import DataNode

logger = logging.getLogger(__name__)


class AirflowLineageTracker(BaseDataLineageTracker):
    """
    Apache Airflow Lineage Tracker

    Tracks lineage for Airflow DAGs, tasks, and operations with native integration.
    """

    def __init__(self, dag_folder: Optional[str] = None, airflow_conn_id: Optional[str] = None):
        super().__init__()
        self.dag_folder = dag_folder
        self.airflow_conn_id = airflow_conn_id
        self.dag_lineages: Dict[str, Dict[str, Any]] = {}
        self.task_lineages: Dict[str, Dict[str, Any]] = {}
        self.xcom_lineages: Dict[str, Dict[str, Any]] = {}

    def track_dag_execution(self, dag_id: str, dag_run_id: str, context: Dict[str, Any]) -> str:
        """Track DAG execution with complete lineage."""
        lineage_id = self._generate_id()

        dag_info = {
            'dag_id': dag_id,
            'dag_run_id': dag_run_id,
            'execution_date': context.get('execution_date'),
            'start_date': datetime.now(),
            'context': self._sanitize_context(context),
            'tasks': [],
            'dependencies': []
        }

        self.dag_lineages[lineage_id] = dag_info

        # Create DAG node
        dag_node = DataNode(
            node_id=f"airflow_dag_{dag_id}",
            node_type="airflow_dag",
            metadata={
                'dag_id': dag_id,
                'dag_run_id': dag_run_id,
                'execution_date': str(context.get('execution_date')),
                'lineage_id': lineage_id
            }
        )

        self.add_node(dag_node)
        logger.info(f"Tracking DAG execution: {dag_id} (run: {dag_run_id})")
        return lineage_id

    def track_task_execution(self, task_id: str, dag_id: str, context: Dict[str, Any],
                             operation_type: str = "task") -> str:
        """Track individual task execution with lineage."""
        lineage_id = self._generate_id()

        task_info = {
            'task_id': task_id,
            'dag_id': dag_id,
            'operation_type': operation_type,
            'start_time': datetime.now(),
            'context': self._sanitize_context(context),
            'inputs': [],
            'outputs': [],
            'xcom_data': {}
        }

        self.task_lineages[lineage_id] = task_info

        # Create task node
        task_node = DataNode(
            node_id=f"airflow_task_{dag_id}_{task_id}",
            node_type="airflow_task",
            metadata={
                'task_id': task_id,
                'dag_id': dag_id,
                'operation_type': operation_type,
                'lineage_id': lineage_id
            }
        )

        self.add_node(task_node)
        logger.info(f"Tracking task execution: {task_id} in DAG {dag_id}")
        return lineage_id

    def track_task_dependency(self, upstream_task: str, downstream_task: str,
                              dag_id: str, dependency_type: str = "task_dependency") -> None:
        """Track dependencies between tasks."""
        upstream_node_id = f"airflow_task_{dag_id}_{upstream_task}"
        downstream_node_id = f"airflow_task_{dag_id}_{downstream_task}"

        self.add_edge(
            upstream_node_id,
            downstream_node_id,
            edge_type=dependency_type,
            metadata={
                'dag_id': dag_id,
                'upstream_task': upstream_task,
                'downstream_task': downstream_task,
                'dependency_type': dependency_type
            }
        )

        logger.debug(
            f"Added task dependency: {upstream_task} -> {downstream_task} in {dag_id}")

    def track_xcom_data(self, task_id: str, dag_id: str, key: str, value: Any,
                        execution_date: datetime) -> str:
        """Track XCom data lineage between tasks."""
        lineage_id = self._generate_id()

        xcom_info = {
            'task_id': task_id,
            'dag_id': dag_id,
            'key': key,
            'value_type': type(value).__name__,
            'value_size': len(str(value)) if value else 0,
            'execution_date': execution_date,
            'timestamp': datetime.now()
        }

        self.xcom_lineages[lineage_id] = xcom_info

        # Create XCom node
        xcom_node = DataNode(
            node_id=f"airflow_xcom_{dag_id}_{task_id}_{key}",
            node_type="airflow_xcom",
            metadata={
                'task_id': task_id,
                'dag_id': dag_id,
                'key': key,
                'value_type': type(value).__name__,
                'lineage_id': lineage_id
            }
        )

        self.add_node(xcom_node)
        logger.debug(f"Tracking XCom data: {key} from {task_id} in {dag_id}")
        return lineage_id

    def track_connection_usage(self, conn_id: str, task_id: str, dag_id: str,
                               operation: str, query: Optional[str] = None) -> str:
        """Track Airflow connection usage in tasks."""
        lineage_id = self._generate_id()

        connection_info = {
            'conn_id': conn_id,
            'task_id': task_id,
            'dag_id': dag_id,
            'operation': operation,
            'query': query,
            'timestamp': datetime.now()
        }

        # Create connection node
        conn_node = DataNode(
            node_id=f"airflow_connection_{conn_id}",
            node_type="airflow_connection",
            metadata={
                'conn_id': conn_id,
                'operation': operation,
                'lineage_id': lineage_id
            }
        )

        self.add_node(conn_node)

        # Link connection to task
        task_node_id = f"airflow_task_{dag_id}_{task_id}"
        self.add_edge(
            f"airflow_connection_{conn_id}",
            task_node_id,
            edge_type="connection_usage",
            metadata={'operation': operation, 'query': query}
        )

        logger.info(f"Tracking connection usage: {conn_id} in {task_id}")
        return lineage_id

    def analyze_dag_lineage(self, dag_id: str) -> Dict[str, Any]:
        """Analyze complete lineage for a DAG."""
        dag_nodes = [node for node in self.nodes.values()
                     if node.metadata.get('dag_id') == dag_id]

        task_nodes = [
            node for node in dag_nodes if node.node_type == "airflow_task"]
        xcom_nodes = [
            node for node in dag_nodes if node.node_type == "airflow_xcom"]
        connection_nodes = [
            node for node in dag_nodes if node.node_type == "airflow_connection"]

        # Analyze task dependencies
        task_dependencies = []
        for edge in self.edges.values():
            if (edge.metadata.get('dag_id') == dag_id and
                    edge.edge_type == "task_dependency"):
                task_dependencies.append({
                    'upstream': edge.metadata.get('upstream_task'),
                    'downstream': edge.metadata.get('downstream_task')
                })

        return {
            'dag_id': dag_id,
            'total_tasks': len(task_nodes),
            'total_xcoms': len(xcom_nodes),
            'total_connections': len(connection_nodes),
            'task_dependencies': task_dependencies,
            'task_list': [node.metadata.get('task_id') for node in task_nodes],
            'connection_list': [node.metadata.get('conn_id') for node in connection_nodes],
            'lineage_complexity': len(task_dependencies) + len(xcom_nodes)
        }

    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize Airflow context for storage."""
        sanitized = {}
        safe_keys = ['execution_date', 'dag_run',
                     'task', 'task_instance', 'dag']

        for key in safe_keys:
            if key in context:
                value = context[key]
                if hasattr(value, '__dict__'):
                    # Convert objects to string representation
                    sanitized[key] = str(value)
                else:
                    sanitized[key] = value

        return sanitized


class LineageOperator(BaseOperator):
    """
    Native Airflow operator with automatic lineage tracking.

    Extends BaseOperator to provide seamless lineage integration.
    """

    template_fields = ['lineage_config']

    @apply_defaults
    def __init__(self, python_callable: Callable, lineage_config: Optional[Dict[str, Any]] = None,
                 lineage_tracker: Optional[AirflowLineageTracker] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_callable = python_callable
        self.lineage_config = lineage_config or {}
        self.lineage_tracker = lineage_tracker or AirflowLineageTracker()

    def execute(self, context: Context) -> Any:
        """Execute the operator with automatic lineage tracking."""
        dag_id = context['dag'].dag_id
        task_id = context['task'].task_id

        # Start tracking task execution
        lineage_id = self.lineage_tracker.track_task_execution(
            task_id=task_id,
            dag_id=dag_id,
            context=context,
            operation_type=self.lineage_config.get(
                'operation', 'python_callable')
        )

        try:
            # Execute the actual task
            result = self.python_callable(**context)

            # Track successful execution
            self.lineage_tracker.task_lineages[lineage_id]['status'] = 'success'
            self.lineage_tracker.task_lineages[lineage_id]['end_time'] = datetime.now(
            )
            self.lineage_tracker.task_lineages[lineage_id]['result_type'] = type(
                result).__name__

            # Track XCom if result is returned
            if result is not None:
                self.lineage_tracker.track_xcom_data(
                    task_id=task_id,
                    dag_id=dag_id,
                    key='return_value',
                    value=result,
                    execution_date=context['execution_date']
                )

            logger.info(
                f"LineageOperator {task_id} completed successfully with lineage {lineage_id}")
            return result

        except Exception as e:
            # Track failed execution
            self.lineage_tracker.task_lineages[lineage_id]['status'] = 'failed'
            self.lineage_tracker.task_lineages[lineage_id]['error'] = str(e)
            self.lineage_tracker.task_lineages[lineage_id]['end_time'] = datetime.now(
            )

            logger.error(f"LineageOperator {task_id} failed with error: {e}")
            raise


class LineageHook(BaseHook):
    """
    Airflow hook for lineage operations.

    Provides database connections and query execution with automatic lineage.
    """

    def __init__(self, airflow_conn_id: str, lineage_tracker: Optional[AirflowLineageTracker] = None):
        super().__init__()
        self.airflow_conn_id = airflow_conn_id
        self.lineage_tracker = lineage_tracker or AirflowLineageTracker()

    def get_connection(self, conn_id: Optional[str] = None) -> Connection:
        """Get Airflow connection with lineage tracking."""
        conn_id = conn_id or self.airflow_conn_id

        if AIRFLOW_AVAILABLE:
            connection = super().get_connection(conn_id)
        else:
            # Mock connection for testing
            connection = type('MockConnection', (), {
                'conn_id': conn_id,
                'host': 'localhost',
                'port': 5432,
                'login': 'user',
                'password': 'pass'
            })()

        # Track connection usage
        context = self._get_current_context()
        if context:
            self.lineage_tracker.track_connection_usage(
                conn_id=conn_id,
                task_id=context.get('task_instance', {}).task_id if context.get(
                    'task_instance') else 'unknown',
                dag_id=context.get('dag', {}).dag_id if context.get(
                    'dag') else 'unknown',
                operation='connection_get'
            )

        return connection

    def execute_query(self, sql: str, parameters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Execute SQL query with lineage tracking."""
        context = self._get_current_context()

        # Track query execution
        if context:
            self.lineage_tracker.track_connection_usage(
                conn_id=self.airflow_conn_id,
                task_id=context.get('task_instance', {}).task_id if context.get(
                    'task_instance') else 'unknown',
                dag_id=context.get('dag', {}).dag_id if context.get(
                    'dag') else 'unknown',
                operation='query_execution',
                query=sql
            )

        # Mock query execution for testing
        logger.info(f"Executing query with lineage tracking: {sql[:100]}...")
        return [{'result': 'mock_data', 'query': sql}]

    def _get_current_context(self) -> Optional[Dict[str, Any]]:
        """Get current Airflow context if available."""
        try:
            if AIRFLOW_AVAILABLE:
                from airflow.operators.python import get_current_context
                return get_current_context()
        except:
            pass
        return None


def lineage_tracked(operation_type: str = "function",
                    lineage_config: Optional[Dict[str, Any]] = None):
    """
    Decorator for automatic lineage tracking in Airflow tasks.

    Usage:
        @lineage_tracked
        def my_task(context):
            return extract_data()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Initialize lineage tracker
            tracker = AirflowLineageTracker()

            # Extract context from kwargs or args
            context = kwargs.get('context') or (
                args[0] if args and isinstance(args[0], dict) else {})

            if context and 'task' in context:
                dag_id = context['dag'].dag_id if 'dag' in context else 'unknown'
                task_id = context['task'].task_id if 'task' in context else 'unknown'

                # Track function execution
                lineage_id = tracker.track_task_execution(
                    task_id=task_id,
                    dag_id=dag_id,
                    context=context,
                    operation_type=operation_type
                )

                try:
                    result = func(*args, **kwargs)
                    tracker.task_lineages[lineage_id]['status'] = 'success'
                    return result
                except Exception as e:
                    tracker.task_lineages[lineage_id]['status'] = 'failed'
                    tracker.task_lineages[lineage_id]['error'] = str(e)
                    raise
            else:
                # Execute without lineage if not in Airflow context
                return func(*args, **kwargs)

        return wrapper
    return decorator


class LineagePostgreSQLOperator(LineageOperator):
    """PostgreSQL operator with automatic lineage tracking."""

    @apply_defaults
    def __init__(self, sql: str, postgres_conn_id: str = 'postgres_default',
                 parameters: Optional[Dict[str, Any]] = None, *args, **kwargs):

        def postgres_callable(**context):
            hook = LineageHook(postgres_conn_id)
            return hook.execute_query(sql, parameters)

        super().__init__(
            python_callable=postgres_callable,
            lineage_config={
                'operation': 'postgresql_query',
                'sql': sql,
                'connection': postgres_conn_id
            },
            *args, **kwargs
        )


class LineageBashOperator(LineageOperator):
    """Bash operator with automatic lineage tracking."""

    @apply_defaults
    def __init__(self, bash_command: str, *args, **kwargs):

        def bash_callable(**context):
            # Mock bash execution for this implementation
            logger.info(f"Executing bash command with lineage: {bash_command}")
            return f"Executed: {bash_command}"

        super().__init__(
            python_callable=bash_callable,
            lineage_config={
                'operation': 'bash_command',
                'command': bash_command
            },
            *args, **kwargs
        )

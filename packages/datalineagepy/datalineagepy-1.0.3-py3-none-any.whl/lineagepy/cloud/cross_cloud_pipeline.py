"""
Cross-cloud pipeline for orchestrating data operations across multiple cloud providers.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
import pandas as pd

from ..core.tracker import LineageTracker
from ..connectors.cloud_base import CloudStorageConnector

logger = logging.getLogger(__name__)


class CrossCloudPipeline:
    """
    Cross-cloud pipeline for building and executing data workflows across cloud providers.

    Features:
    - Extract, Transform, Load (ETL) operations across clouds
    - Pipeline chaining and composition
    - Automatic lineage tracking for all operations
    - Error handling and rollback capabilities
    - Performance monitoring and optimization
    """

    def __init__(self,
                 cloud_connectors: Dict[str, CloudStorageConnector],
                 tracker: LineageTracker,
                 pipeline_name: str = None):
        """
        Initialize cross-cloud pipeline.

        Args:
            cloud_connectors: Dict of cloud_name -> connector mappings
            tracker: LineageTracker instance
            pipeline_name: Optional pipeline name for tracking
        """
        self.cloud_connectors = cloud_connectors
        self.tracker = tracker
        self.pipeline_name = pipeline_name or f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Pipeline state
        self.steps = []
        self.executed = False
        self.execution_results = {}
        self.current_data = None

    def extract(self, cloud_path: str, **kwargs) -> 'CrossCloudPipeline':
        """
        Extract data from cloud storage.

        Args:
            cloud_path: Path in format 'cloud:path'
            **kwargs: Additional read options

        Returns:
            Self for method chaining
        """
        self.steps.append({
            'type': 'extract',
            'cloud_path': cloud_path,
            'kwargs': kwargs,
            'timestamp': datetime.now().isoformat()
        })
        return self

    def transform(self, transform_func: Callable[[pd.DataFrame], pd.DataFrame],
                  transform_name: str = None, **kwargs) -> 'CrossCloudPipeline':
        """
        Add transformation step to pipeline.

        Args:
            transform_func: Function that takes DataFrame and returns DataFrame
            transform_name: Optional name for the transformation
            **kwargs: Additional transformation options

        Returns:
            Self for method chaining
        """
        self.steps.append({
            'type': 'transform',
            'function': transform_func,
            'name': transform_name or transform_func.__name__,
            'kwargs': kwargs,
            'timestamp': datetime.now().isoformat()
        })
        return self

    def load(self, cloud_path: str, **kwargs) -> 'CrossCloudPipeline':
        """
        Load data to cloud storage.

        Args:
            cloud_path: Path in format 'cloud:path'
            **kwargs: Additional write options

        Returns:
            Self for method chaining
        """
        self.steps.append({
            'type': 'load',
            'cloud_path': cloud_path,
            'kwargs': kwargs,
            'timestamp': datetime.now().isoformat()
        })
        return self

    def backup(self, cloud_path: str, **kwargs) -> 'CrossCloudPipeline':
        """
        Create backup copy in cloud storage.

        Args:
            cloud_path: Path in format 'cloud:path'
            **kwargs: Additional backup options

        Returns:
            Self for method chaining
        """
        self.steps.append({
            'type': 'backup',
            'cloud_path': cloud_path,
            'kwargs': kwargs,
            'timestamp': datetime.now().isoformat()
        })
        return self

    def validate(self, validation_func: Callable[[pd.DataFrame], bool],
                 validation_name: str = None, **kwargs) -> 'CrossCloudPipeline':
        """
        Add data validation step.

        Args:
            validation_func: Function that takes DataFrame and returns bool
            validation_name: Optional name for validation
            **kwargs: Additional validation options

        Returns:
            Self for method chaining
        """
        self.steps.append({
            'type': 'validate',
            'function': validation_func,
            'name': validation_name or validation_func.__name__,
            'kwargs': kwargs,
            'timestamp': datetime.now().isoformat()
        })
        return self

    def branch(self, condition_func: Callable[[pd.DataFrame], bool],
               true_pipeline: 'CrossCloudPipeline',
               false_pipeline: 'CrossCloudPipeline' = None) -> 'CrossCloudPipeline':
        """
        Add conditional branching to pipeline.

        Args:
            condition_func: Function that evaluates condition
            true_pipeline: Pipeline to execute if condition is True
            false_pipeline: Pipeline to execute if condition is False

        Returns:
            Self for method chaining
        """
        self.steps.append({
            'type': 'branch',
            'condition': condition_func,
            'true_pipeline': true_pipeline,
            'false_pipeline': false_pipeline,
            'timestamp': datetime.now().isoformat()
        })
        return self

    def parallel(self, pipelines: List['CrossCloudPipeline']) -> 'CrossCloudPipeline':
        """
        Execute multiple pipelines in parallel.

        Args:
            pipelines: List of pipelines to execute in parallel

        Returns:
            Self for method chaining
        """
        self.steps.append({
            'type': 'parallel',
            'pipelines': pipelines,
            'timestamp': datetime.now().isoformat()
        })
        return self

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute the pipeline.

        Args:
            dry_run: If True, simulate execution without actually running

        Returns:
            Execution results
        """
        if self.executed and not dry_run:
            raise RuntimeError("Pipeline has already been executed")

        execution_start = datetime.now()
        results = {
            'pipeline_name': self.pipeline_name,
            'started_at': execution_start.isoformat(),
            'dry_run': dry_run,
            'steps': [],
            'success': True,
            'error': None
        }

        try:
            # Track pipeline start
            if self.tracker and not dry_run:
                self.tracker.add_operation_context(
                    operation_name="pipeline_start",
                    context={
                        'pipeline_name': self.pipeline_name,
                        'steps_count': len(self.steps),
                        'dry_run': dry_run
                    }
                )

            # Execute each step
            for i, step in enumerate(self.steps):
                step_start = datetime.now()
                step_result = {
                    'step_index': i,
                    'step_type': step['type'],
                    'started_at': step_start.isoformat(),
                    'success': True,
                    'error': None
                }

                try:
                    if dry_run:
                        step_result['simulated'] = True
                        step_result['description'] = self._describe_step(step)
                    else:
                        step_result.update(self._execute_step(step))

                    step_result['completed_at'] = datetime.now().isoformat()
                    step_result['duration_seconds'] = (
                        datetime.now() - step_start
                    ).total_seconds()

                except Exception as e:
                    step_result['success'] = False
                    step_result['error'] = str(e)
                    step_result['completed_at'] = datetime.now().isoformat()

                    logger.error(f"Pipeline step {i} failed: {str(e)}")

                    # Stop execution on first error
                    results['success'] = False
                    results['error'] = f"Step {i} failed: {str(e)}"
                    break

                results['steps'].append(step_result)

            results['completed_at'] = datetime.now().isoformat()
            results['total_duration_seconds'] = (
                datetime.now() - execution_start
            ).total_seconds()

            # Track pipeline completion
            if self.tracker and not dry_run:
                self.tracker.add_operation_context(
                    operation_name="pipeline_complete",
                    context={
                        'pipeline_name': self.pipeline_name,
                        'success': results['success'],
                        'duration_seconds': results['total_duration_seconds'],
                        'steps_executed': len(results['steps'])
                    }
                )

            if not dry_run:
                self.executed = True
                self.execution_results = results

            return results

        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            results['completed_at'] = datetime.now().isoformat()
            logger.error(f"Pipeline execution failed: {str(e)}")
            raise

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual pipeline step."""
        step_type = step['type']
        result = {}

        if step_type == 'extract':
            cloud_path = step['cloud_path']
            kwargs = step['kwargs']

            # Parse cloud path
            cloud_name, object_key = self._parse_cloud_path(cloud_path)
            connector = self.cloud_connectors[cloud_name]

            # Read data based on file extension
            if object_key.endswith('.parquet'):
                self.current_data = connector.read_parquet(
                    object_key, **kwargs)
            elif object_key.endswith('.csv'):
                self.current_data = connector.read_csv(object_key, **kwargs)
            elif object_key.endswith('.json'):
                self.current_data = connector.read_json(object_key, **kwargs)
            else:
                raise ValueError(f"Unsupported file format: {object_key}")

            result.update({
                'cloud_path': cloud_path,
                'rows_extracted': len(self.current_data),
                'columns_extracted': len(self.current_data.columns)
            })

        elif step_type == 'transform':
            if self.current_data is None:
                raise RuntimeError("No data available for transformation")

            transform_func = step['function']
            kwargs = step['kwargs']

            # Apply transformation
            old_shape = self.current_data.shape
            self.current_data = transform_func(self.current_data, **kwargs)
            new_shape = self.current_data.shape

            result.update({
                'transform_name': step['name'],
                'input_shape': old_shape,
                'output_shape': new_shape,
                'rows_changed': new_shape[0] - old_shape[0],
                'columns_changed': new_shape[1] - old_shape[1]
            })

        elif step_type == 'load':
            if self.current_data is None:
                raise RuntimeError("No data available for loading")

            cloud_path = step['cloud_path']
            kwargs = step['kwargs']

            # Parse cloud path
            cloud_name, object_key = self._parse_cloud_path(cloud_path)
            connector = self.cloud_connectors[cloud_name]

            # Write data based on file extension
            if object_key.endswith('.parquet'):
                success = connector.write_parquet(
                    self.current_data, object_key, **kwargs)
            elif object_key.endswith('.csv'):
                success = connector.write_csv(
                    self.current_data, object_key, **kwargs)
            elif object_key.endswith('.json'):
                success = connector.write_json(
                    self.current_data, object_key, **kwargs)
            else:
                raise ValueError(f"Unsupported file format: {object_key}")

            result.update({
                'cloud_path': cloud_path,
                'rows_loaded': len(self.current_data),
                'columns_loaded': len(self.current_data.columns),
                'success': success
            })

        elif step_type == 'backup':
            if self.current_data is None:
                raise RuntimeError("No data available for backup")

            cloud_path = step['cloud_path']
            kwargs = step['kwargs']

            # Parse cloud path
            cloud_name, object_key = self._parse_cloud_path(cloud_path)
            connector = self.cloud_connectors[cloud_name]

            # Create backup
            if object_key.endswith('.parquet'):
                success = connector.write_parquet(
                    self.current_data, object_key, **kwargs)
            elif object_key.endswith('.csv'):
                success = connector.write_csv(
                    self.current_data, object_key, **kwargs)
            elif object_key.endswith('.json'):
                success = connector.write_json(
                    self.current_data, object_key, **kwargs)
            else:
                raise ValueError(f"Unsupported file format: {object_key}")

            result.update({
                'backup_path': cloud_path,
                'rows_backed_up': len(self.current_data),
                'success': success
            })

        elif step_type == 'validate':
            if self.current_data is None:
                raise RuntimeError("No data available for validation")

            validation_func = step['function']
            kwargs = step['kwargs']

            # Run validation
            is_valid = validation_func(self.current_data, **kwargs)

            result.update({
                'validation_name': step['name'],
                'is_valid': is_valid,
                'rows_validated': len(self.current_data)
            })

            if not is_valid:
                raise ValueError(f"Data validation failed: {step['name']}")

        elif step_type == 'branch':
            if self.current_data is None:
                raise RuntimeError("No data available for branching")

            condition_func = step['condition']
            condition_result = condition_func(self.current_data)

            if condition_result:
                pipeline = step['true_pipeline']
                pipeline.current_data = self.current_data.copy()
                branch_result = pipeline.execute()
                self.current_data = pipeline.current_data
            else:
                pipeline = step.get('false_pipeline')
                if pipeline:
                    pipeline.current_data = self.current_data.copy()
                    branch_result = pipeline.execute()
                    self.current_data = pipeline.current_data
                else:
                    branch_result = {'skipped': True}

            result.update({
                'condition_result': condition_result,
                'branch_executed': 'true' if condition_result else 'false',
                'branch_result': branch_result
            })

        elif step_type == 'parallel':
            pipelines = step['pipelines']
            parallel_results = []

            for pipeline in pipelines:
                pipeline.current_data = self.current_data.copy()
                parallel_result = pipeline.execute()
                parallel_results.append(parallel_result)

            result.update({
                'pipelines_count': len(pipelines),
                'parallel_results': parallel_results
            })

        return result

    def _describe_step(self, step: Dict[str, Any]) -> str:
        """Describe step for dry run."""
        step_type = step['type']

        if step_type == 'extract':
            return f"Extract data from {step['cloud_path']}"
        elif step_type == 'transform':
            return f"Apply transformation: {step['name']}"
        elif step_type == 'load':
            return f"Load data to {step['cloud_path']}"
        elif step_type == 'backup':
            return f"Backup data to {step['cloud_path']}"
        elif step_type == 'validate':
            return f"Validate data with: {step['name']}"
        elif step_type == 'branch':
            return "Execute conditional branching"
        elif step_type == 'parallel':
            return f"Execute {len(step['pipelines'])} pipelines in parallel"
        else:
            return f"Unknown step type: {step_type}"

    def _parse_cloud_path(self, cloud_path: str) -> tuple:
        """Parse cloud path into provider and object key."""
        if ':' not in cloud_path:
            raise ValueError(f"Invalid cloud path format: {cloud_path}")

        parts = cloud_path.split(':', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid cloud path format: {cloud_path}")

        cloud_name, object_key = parts
        if cloud_name not in self.cloud_connectors:
            raise ValueError(f"Unknown cloud provider: {cloud_name}")

        return cloud_name, object_key

    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get pipeline summary information."""
        return {
            'pipeline_name': self.pipeline_name,
            'steps_count': len(self.steps),
            'step_types': [step['type'] for step in self.steps],
            'executed': self.executed,
            'has_current_data': self.current_data is not None,
            'current_data_shape': self.current_data.shape if self.current_data is not None else None
        }

    def reset(self) -> None:
        """Reset pipeline state for re-execution."""
        self.executed = False
        self.execution_results = {}
        self.current_data = None

    def __str__(self) -> str:
        return f"CrossCloudPipeline(name={self.pipeline_name}, steps={len(self.steps)})"

    def __repr__(self) -> str:
        return self.__str__()

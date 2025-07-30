"""
DataLineagePy Phase 9: Orchestration Integration Simple Demo

This demo showcases the Phase 9 orchestration capabilities without requiring
optional dependencies, using mock implementations to demonstrate the features.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("🎉 DataLineagePy Phase 9: Orchestration Integration Simple Demo")
print("=" * 70)
print("Demonstrating orchestration lineage capabilities (dependency-free)!")
print()

# Test Universal Orchestration Manager
try:
    from lineagepy.orchestration.universal_orchestration import (
        UniversalOrchestrationManager,
        CrossPlatformWorkflow,
        OrchestrationPlatform,
        WorkflowStage
    )

    print("✅ Universal Orchestration Manager available")

    # Create orchestration manager
    orchestration_manager = UniversalOrchestrationManager()

    # Create a cross-platform workflow
    workflow = orchestration_manager.create_cross_platform_workflow(
        workflow_id='demo_workflow',
        name='Phase 9 Demo Workflow',
        description='Demonstration of cross-platform orchestration'
    )

    # Add stages for different platforms
    airflow_stage = orchestration_manager.add_airflow_stage(
        workflow_id=workflow.workflow_id,
        stage_id='extract_data',
        dag_id='demo_dag',
        task_id='extract_users'
    )

    dbt_stage = orchestration_manager.add_dbt_stage(
        workflow_id=workflow.workflow_id,
        stage_id='transform_data',
        project='demo_project',
        model='user_analytics'
    )

    prefect_stage = orchestration_manager.add_prefect_stage(
        workflow_id=workflow.workflow_id,
        stage_id='process_data',
        flow_name='analytics_flow',
        deployment='production'
    )

    # Add dependencies
    orchestration_manager.add_stage_dependency(
        workflow_id=workflow.workflow_id,
        upstream_stage='extract_data',
        downstream_stage='transform_data'
    )

    orchestration_manager.add_stage_dependency(
        workflow_id=workflow.workflow_id,
        upstream_stage='transform_data',
        downstream_stage='process_data'
    )

    print(f"📋 Created workflow with {len(workflow.stages)} stages")
    print(f"🔧 Platforms: {[p.value for p in workflow.platforms]}")

    # Execute the workflow
    results = orchestration_manager.execute_workflow(workflow.workflow_id)

    print(f"✅ Workflow executed: {results['status']}")
    print(f"   Duration: {results['execution_duration']}")
    print(
        f"   Completed stages: {results['completed_stages']}/{results['total_stages']}")

    # Analyze dependencies
    analysis = orchestration_manager.analyze_cross_platform_dependencies()
    print(f"📊 Cross-platform analysis:")
    print(f"   Total workflows: {analysis['total_workflows']}")
    print(f"   Complexity score: {analysis['complexity_score']}")

except ImportError as e:
    print(f"❌ Universal Orchestration Manager not available: {e}")

print()

# Test individual platform components
print("🔧 Testing Platform Components:")
print("-" * 40)

# Test Airflow integration
try:
    from lineagepy.orchestration.airflow_lineage import AirflowLineageTracker

    airflow_tracker = AirflowLineageTracker()

    # Mock DAG context
    mock_context = {
        'dag': type('MockDAG', (), {'dag_id': 'demo_dag'})(),
        'task': type('MockTask', (), {'task_id': 'demo_task'})(),
        'execution_date': datetime.now()
    }

    # Track a DAG execution
    dag_lineage_id = airflow_tracker.track_dag_execution(
        dag_id='demo_dag',
        dag_run_id='demo_run_001',
        context=mock_context
    )

    # Track task execution
    task_lineage_id = airflow_tracker.track_task_execution(
        task_id='demo_task',
        dag_id='demo_dag',
        context=mock_context
    )

    print(
        f"✅ Airflow: DAG lineage {dag_lineage_id[:8]}..., Task lineage {task_lineage_id[:8]}...")

except ImportError as e:
    print(f"❌ Airflow integration not available: {e}")

# Test dbt integration
try:
    from lineagepy.orchestration.dbt_lineage import DbtLineageTracker, dbt_lineage_macro

    dbt_tracker = DbtLineageTracker(project_dir="./mock_project")

    # Mock model configuration
    mock_model = {
        'name': 'demo_model',
        'schema': 'analytics',
        'description': 'Demo model for Phase 9',
        'columns': {'id': {}, 'name': {}, 'value': {}},
        'config': {'materialized': 'table'}
    }

    # Track model lineage
    model_lineage_id = dbt_tracker.track_model_lineage(
        model_name='demo_model',
        model_config=mock_model
    )

    # Track dbt run
    run_lineage_id = dbt_tracker.track_dbt_run(
        command='dbt run --models demo_model',
        target='dev',
        models=['demo_model']
    )

    # Complete the run
    dbt_tracker.complete_dbt_run(run_lineage_id, status='success')

    # Generate macro
    macro_code = dbt_lineage_macro()

    print(
        f"✅ dbt: Model lineage {model_lineage_id[:8]}..., Run {run_lineage_id[:8]}...")
    print(f"   Generated macro: {len(macro_code)} characters")

except ImportError as e:
    print(f"❌ dbt integration not available: {e}")

# Test Prefect integration
try:
    from lineagepy.orchestration.prefect_lineage import (
        PrefectLineageTracker,
        lineage_tracked_flow,
        lineage_tracked_task
    )

    prefect_tracker = PrefectLineageTracker()

    # Track flow execution
    flow_lineage_id = prefect_tracker.track_flow_execution(
        flow_name='demo_flow',
        deployment_name='demo_deployment',
        parameters={'env': 'demo'}
    )

    # Track task execution
    task_lineage_id = prefect_tracker.track_task_execution(
        task_name='demo_task',
        flow_name='demo_flow',
        task_inputs=['input_data'],
        task_outputs=['processed_data']
    )

    # Complete flow
    prefect_tracker.complete_flow_run(
        lineage_id=flow_lineage_id,
        status='Completed',
        final_state='SUCCESS'
    )

    # Test decorators
    @lineage_tracked_flow
    def demo_flow():
        return "Flow executed"

    @lineage_tracked_task
    def demo_task():
        return {"data": "processed"}

    flow_result = demo_flow()
    task_result = demo_task()

    print(
        f"✅ Prefect: Flow lineage {flow_lineage_id[:8]}..., Task lineage {task_lineage_id[:8]}...")
    print(f"   Decorator results: {flow_result}, {task_result['data']}")

except ImportError as e:
    print(f"❌ Prefect integration not available: {e}")

print()

# Test orchestration status
try:
    from lineagepy.orchestration import (
        print_orchestration_status,
        get_orchestration_info,
        get_available_platforms
    )

    print("📋 Orchestration Platform Status:")
    print("-" * 40)
    print_orchestration_status()

    print("\n📊 Available Platforms:")
    platforms = get_available_platforms()
    for platform in platforms:
        print(f"   • {platform}")

    print("\n🔍 Detailed Information:")
    info = get_orchestration_info()
    print(f"   Total platforms: {info['total_platforms']}")
    print(f"   Enterprise ready: {info['enterprise_ready']}")

    print("\n💡 Recommendations:")
    for rec in info['recommendations'][:3]:  # Show first 3
        print(f"   • {rec}")

except ImportError as e:
    print(f"❌ Orchestration status functions not available: {e}")

print()
print("🎉 Phase 9 Simple Demo Completed!")
print("=" * 70)
print("✅ Universal Orchestration: Cross-platform workflow management")
print("✅ Platform Components: Airflow, dbt, Prefect integration")
print("✅ Lineage Tracking: Complete workflow lineage capture")
print("✅ Status Reporting: Platform availability and recommendations")
print()
print("🚀 DataLineagePy Phase 9: Native orchestration integration ready!")
print("🔧 Transform your workflow governance with universal lineage! ⚡")

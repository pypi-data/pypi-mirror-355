"""
Distributed Cluster Management

Core cluster management for enterprise-scale lineage deployments with
automatic scaling, health monitoring, and distributed coordination.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from ..config import EnterpriseConfig, ClusterConfig
from ..exceptions import (
    ClusterError, ClusterNodeError, ClusterQuorumError,
    ClusterSplitBrainError, ScalabilityError
)

logger = logging.getLogger(__name__)


@dataclass
class ClusterNode:
    """Represents a single node in the lineage cluster."""
    node_id: str
    address: str
    port: int
    status: str = "unknown"  # unknown, healthy, unhealthy, failed
    last_heartbeat: Optional[datetime] = None
    load_score: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    storage_usage: float = 0.0
    partition_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def endpoint(self) -> str:
        """Get the full endpoint URL for this node."""
        return f"http://{self.address}:{self.port}"

    @property
    def is_healthy(self) -> bool:
        """Check if node is considered healthy."""
        if self.status != "healthy":
            return False
        if not self.last_heartbeat:
            return False
        # Consider healthy if heartbeat within last 60 seconds
        return datetime.now() - self.last_heartbeat < timedelta(seconds=60)


@dataclass
class ClusterStatus:
    """Current status of the lineage cluster."""
    cluster_id: str
    total_nodes: int
    healthy_nodes: int
    unhealthy_nodes: int
    failed_nodes: int
    quorum_size: int
    has_quorum: bool
    leader_node: Optional[str]
    total_partitions: int
    replicated_partitions: int
    under_replicated_partitions: int
    cluster_health: str  # healthy, degraded, critical, failed
    last_updated: datetime = field(default_factory=datetime.now)


class LineageCluster:
    """
    Enterprise-grade distributed lineage cluster management.

    Provides distributed coordination, automatic scaling, health monitoring,
    and high availability for petabyte-scale lineage deployments.
    """

    def __init__(
        self,
        name: str = "lineagepy-cluster",
        nodes: Optional[List[str]] = None,
        storage_backend: str = "postgresql",
        replication_factor: int = 3,
        sharding_strategy: str = "consistent_hash",
        auto_scaling: bool = True,
        config: Optional[ClusterConfig] = None
    ):
        self.cluster_id = str(uuid.uuid4())
        self.name = name
        self.storage_backend = storage_backend
        self.replication_factor = replication_factor
        self.sharding_strategy = sharding_strategy
        self.auto_scaling = auto_scaling

        # Use provided config or create default
        self.config = config or ClusterConfig()
        if nodes:
            self.config.nodes = nodes

        # Cluster state
        self.nodes: Dict[str, ClusterNode] = {}
        # partition_id -> [node_ids]
        self.partitions: Dict[int, List[str]] = {}
        self.leader_node: Optional[str] = None
        self.is_deployed = False
        self.deployment_time: Optional[datetime] = None

        # Monitoring and management
        self.health_monitor = None
        self.load_balancer = None
        self.consensus_manager = None

        logger.info(
            f"Initialized LineageCluster '{name}' with {len(self.config.nodes)} nodes")

    async def deploy(self) -> None:
        """Deploy the lineage cluster."""
        try:
            logger.info(
                f"Deploying cluster '{self.name}' with {len(self.config.nodes)} nodes")

            # Initialize cluster nodes
            await self._initialize_nodes()

            # Set up distributed storage
            await self._setup_distributed_storage()

            # Start health monitoring
            await self._start_health_monitoring()

            # Initialize consensus
            await self._initialize_consensus()

            # Set up partitioning
            await self._setup_partitioning()

            # Start load balancer
            await self._start_load_balancer()

            self.is_deployed = True
            self.deployment_time = datetime.now()

            logger.info(f"Cluster '{self.name}' deployed successfully")

        except Exception as e:
            logger.error(f"Failed to deploy cluster '{self.name}': {e}")
            raise ClusterError(f"Cluster deployment failed: {e}")

    async def _initialize_nodes(self) -> None:
        """Initialize all cluster nodes."""
        for node_address in self.config.nodes:
            try:
                # Parse node address
                if ':' in node_address:
                    address, port_str = node_address.split(':')
                    port = int(port_str)
                else:
                    address = node_address
                    port = 8080  # Default port

                # Create node instance
                node_id = f"{address}:{port}"
                node = ClusterNode(
                    node_id=node_id,
                    address=address,
                    port=port,
                    status="initializing"
                )

                # Initialize node
                await self._initialize_single_node(node)
                self.nodes[node_id] = node

                logger.info(f"Initialized node {node_id}")

            except Exception as e:
                logger.error(f"Failed to initialize node {node_address}: {e}")
                raise ClusterNodeError(
                    f"Node initialization failed: {e}",
                    node_id=node_address
                )

    async def _initialize_single_node(self, node: ClusterNode) -> None:
        """Initialize a single cluster node."""
        # In a real implementation, this would:
        # 1. Install lineagepy on the node
        # 2. Configure the node for cluster operation
        # 3. Start the lineage service
        # 4. Verify node is responding

        # Simulate node initialization
        await asyncio.sleep(0.1)

        node.status = "healthy"
        node.last_heartbeat = datetime.now()
        node.metadata = {
            'cluster_id': self.cluster_id,
            'cluster_name': self.name,
            'node_version': '2.0.0',
            'capabilities': ['lineage_tracking', 'query_processing', 'storage']
        }

    async def _setup_distributed_storage(self) -> None:
        """Set up distributed storage backend."""
        logger.info("Setting up distributed storage")

        # Configure storage for each node
        for node in self.nodes.values():
            storage_config = {
                'backend': self.storage_backend,
                'cluster_id': self.cluster_id,
                'node_id': node.node_id,
                'replication_factor': self.replication_factor
            }
            node.metadata['storage_config'] = storage_config

        logger.info("Distributed storage configured")

    async def _start_health_monitoring(self) -> None:
        """Start health monitoring for all nodes."""
        from .health_monitor import HealthMonitor

        self.health_monitor = HealthMonitor(self)
        await self.health_monitor.start()
        logger.info("Health monitoring started")

    async def _initialize_consensus(self) -> None:
        """Initialize consensus mechanism for cluster coordination."""
        from .consensus import RaftConsensus

        self.consensus_manager = RaftConsensus(self)
        await self.consensus_manager.initialize()

        # Elect initial leader
        self.leader_node = await self.consensus_manager.elect_leader()
        logger.info(f"Cluster leader elected: {self.leader_node}")

    async def _setup_partitioning(self) -> None:
        """Set up data partitioning across cluster nodes."""
        from .partitioning import ConsistentHashPartitioner

        partitioner = ConsistentHashPartitioner(
            nodes=list(self.nodes.keys()),
            replication_factor=self.replication_factor
        )

        self.partitions = partitioner.create_partitions(num_partitions=1024)

        # Update node partition counts
        for partition_nodes in self.partitions.values():
            for node_id in partition_nodes:
                if node_id in self.nodes:
                    self.nodes[node_id].partition_count += 1

        logger.info(
            f"Created {len(self.partitions)} partitions across {len(self.nodes)} nodes")

    async def _start_load_balancer(self) -> None:
        """Start load balancer for request distribution."""
        from .load_balancer import LoadBalancer

        self.load_balancer = LoadBalancer(
            cluster=self,
            strategy=self.config.load_balancer_type
        )
        await self.load_balancer.start()
        logger.info("Load balancer started")

    def get_status(self) -> ClusterStatus:
        """Get current cluster status."""
        healthy_nodes = sum(
            1 for node in self.nodes.values() if node.is_healthy)
        unhealthy_nodes = sum(
            1 for node in self.nodes.values() if node.status == "unhealthy")
        failed_nodes = sum(1 for node in self.nodes.values()
                           if node.status == "failed")

        quorum_size = len(self.nodes) // 2 + 1
        has_quorum = healthy_nodes >= quorum_size

        # Calculate partition health
        replicated_partitions = sum(
            1 for nodes in self.partitions.values()
            if len([n for n in nodes if n in self.nodes and self.nodes[n].is_healthy]) >= self.replication_factor
        )
        under_replicated = len(self.partitions) - replicated_partitions

        # Determine overall cluster health
        if failed_nodes > 0 or not has_quorum:
            cluster_health = "critical"
        elif unhealthy_nodes > 0 or under_replicated > 0:
            cluster_health = "degraded"
        elif healthy_nodes == len(self.nodes):
            cluster_health = "healthy"
        else:
            cluster_health = "degraded"

        return ClusterStatus(
            cluster_id=self.cluster_id,
            total_nodes=len(self.nodes),
            healthy_nodes=healthy_nodes,
            unhealthy_nodes=unhealthy_nodes,
            failed_nodes=failed_nodes,
            quorum_size=quorum_size,
            has_quorum=has_quorum,
            leader_node=self.leader_node,
            total_partitions=len(self.partitions),
            replicated_partitions=replicated_partitions,
            under_replicated_partitions=under_replicated,
            cluster_health=cluster_health
        )

    async def scale_up(self, target_nodes: int) -> None:
        """Scale up the cluster to target number of nodes."""
        current_nodes = len(self.nodes)
        if target_nodes <= current_nodes:
            logger.warning(
                f"Target nodes ({target_nodes}) not greater than current ({current_nodes})")
            return

        logger.info(
            f"Scaling cluster from {current_nodes} to {target_nodes} nodes")

        try:
            # Add new nodes (this would provision new infrastructure in real implementation)
            new_nodes = []
            for i in range(current_nodes, target_nodes):
                new_node_address = f"node-{i}:8080"
                new_nodes.append(new_node_address)

            # Initialize new nodes
            for node_address in new_nodes:
                address, port_str = node_address.split(':')
                port = int(port_str)

                node = ClusterNode(
                    node_id=node_address,
                    address=address,
                    port=port,
                    status="initializing"
                )

                await self._initialize_single_node(node)
                self.nodes[node_address] = node

            # Rebalance partitions
            await self._rebalance_partitions()

            logger.info(
                f"Successfully scaled cluster to {len(self.nodes)} nodes")

        except Exception as e:
            logger.error(f"Failed to scale cluster: {e}")
            raise ScalabilityError(
                f"Cluster scaling failed: {e}",
                limit_type="node_count",
                current_value=current_nodes,
                max_value=target_nodes
            )

    async def scale_down(self, target_nodes: int) -> None:
        """Scale down the cluster to target number of nodes."""
        current_nodes = len(self.nodes)
        if target_nodes >= current_nodes:
            logger.warning(
                f"Target nodes ({target_nodes}) not less than current ({current_nodes})")
            return

        if target_nodes < 3:
            raise ClusterError("Cannot scale below 3 nodes (minimum for HA)")

        logger.info(
            f"Scaling cluster from {current_nodes} to {target_nodes} nodes")

        # Select nodes to remove (prefer unhealthy nodes)
        nodes_to_remove = []
        healthy_nodes = [n for n in self.nodes.values() if n.is_healthy]
        unhealthy_nodes = [n for n in self.nodes.values() if not n.is_healthy]

        # Remove unhealthy nodes first
        for node in unhealthy_nodes:
            if len(nodes_to_remove) < (current_nodes - target_nodes):
                nodes_to_remove.append(node)

        # Remove additional healthy nodes if needed
        for node in healthy_nodes:
            if len(nodes_to_remove) < (current_nodes - target_nodes):
                nodes_to_remove.append(node)

        # Migrate data from nodes being removed
        await self._migrate_node_data(nodes_to_remove)

        # Remove nodes
        for node in nodes_to_remove:
            del self.nodes[node.node_id]

        # Rebalance remaining partitions
        await self._rebalance_partitions()

        logger.info(f"Successfully scaled cluster to {len(self.nodes)} nodes")

    async def _rebalance_partitions(self) -> None:
        """Rebalance partitions across available nodes."""
        from .partitioning import ConsistentHashPartitioner

        partitioner = ConsistentHashPartitioner(
            nodes=list(self.nodes.keys()),
            replication_factor=self.replication_factor
        )

        new_partitions = partitioner.create_partitions(
            num_partitions=len(self.partitions))

        # Calculate data movements needed
        movements = []
        for partition_id, old_nodes in self.partitions.items():
            new_nodes = new_partitions[partition_id]
            for old_node in old_nodes:
                if old_node not in new_nodes:
                    # Need to move data from old_node
                    target_node = None
                    for new_node in new_nodes:
                        if new_node not in old_nodes:
                            target_node = new_node
                            break
                    if target_node:
                        movements.append((partition_id, old_node, target_node))

        # Execute data movements
        for partition_id, source_node, target_node in movements:
            await self._move_partition_data(partition_id, source_node, target_node)

        # Update partition assignments
        self.partitions = new_partitions

        # Update node partition counts
        for node in self.nodes.values():
            node.partition_count = 0
        for partition_nodes in self.partitions.values():
            for node_id in partition_nodes:
                if node_id in self.nodes:
                    self.nodes[node_id].partition_count += 1

        logger.info("Partition rebalancing completed")

    async def _migrate_node_data(self, nodes_to_remove: List[ClusterNode]) -> None:
        """Migrate data from nodes being removed."""
        for node in nodes_to_remove:
            logger.info(f"Migrating data from node {node.node_id}")

            # Find partitions on this node
            node_partitions = [
                partition_id for partition_id, nodes in self.partitions.items()
                if node.node_id in nodes
            ]

            # For each partition, ensure data is replicated to other nodes
            for partition_id in node_partitions:
                await self._ensure_partition_replication(partition_id, exclude_node=node.node_id)

        logger.info(
            f"Data migration completed for {len(nodes_to_remove)} nodes")

    async def _move_partition_data(self, partition_id: int, source_node: str, target_node: str) -> None:
        """Move partition data from source to target node."""
        logger.debug(
            f"Moving partition {partition_id} from {source_node} to {target_node}")

        # In real implementation, this would:
        # 1. Copy partition data from source to target
        # 2. Verify data integrity
        # 3. Update partition assignments
        # 4. Remove data from source

        # Simulate data movement
        await asyncio.sleep(0.01)

    async def _ensure_partition_replication(self, partition_id: int, exclude_node: str) -> None:
        """Ensure partition has sufficient replication excluding specified node."""
        current_nodes = [
            n for n in self.partitions[partition_id] if n != exclude_node]

        if len(current_nodes) < self.replication_factor:
            # Need to add more replicas
            available_nodes = [n for n in self.nodes.keys(
            ) if n not in self.partitions[partition_id]]

            for i in range(self.replication_factor - len(current_nodes)):
                if available_nodes:
                    target_node = available_nodes.pop(0)
                    await self._move_partition_data(partition_id, exclude_node, target_node)
                    current_nodes.append(target_node)

    async def rolling_update(self, image: str, batch_size: int = 1) -> None:
        """Perform rolling update of cluster nodes."""
        logger.info(f"Starting rolling update to image {image}")

        node_list = list(self.nodes.values())

        # Update nodes in batches
        for i in range(0, len(node_list), batch_size):
            batch = node_list[i:i + batch_size]

            logger.info(
                f"Updating batch {i//batch_size + 1}: {[n.node_id for n in batch]}")

            # Update each node in the batch
            for node in batch:
                await self._update_single_node(node, image)

            # Wait for batch to be healthy before continuing
            await self._wait_for_nodes_healthy([n.node_id for n in batch])

        logger.info("Rolling update completed successfully")

    async def _update_single_node(self, node: ClusterNode, image: str) -> None:
        """Update a single node to new image."""
        logger.info(f"Updating node {node.node_id} to {image}")

        # Mark node as updating
        node.status = "updating"

        # In real implementation, this would:
        # 1. Drain node of traffic
        # 2. Stop old container/service
        # 3. Start new container/service with new image
        # 4. Verify new service is healthy

        # Simulate update process
        await asyncio.sleep(2.0)

        # Update node metadata
        node.status = "healthy"
        node.last_heartbeat = datetime.now()
        node.metadata['image'] = image

        logger.info(f"Node {node.node_id} updated successfully")

    async def _wait_for_nodes_healthy(self, node_ids: List[str], timeout: int = 300) -> None:
        """Wait for specified nodes to become healthy."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            all_healthy = all(
                self.nodes[node_id].is_healthy for node_id in node_ids
                if node_id in self.nodes
            )

            if all_healthy:
                return

            await asyncio.sleep(5)

        unhealthy_nodes = [
            node_id for node_id in node_ids
            if node_id in self.nodes and not self.nodes[node_id].is_healthy
        ]

        raise ClusterError(
            f"Nodes failed to become healthy: {unhealthy_nodes}")

    async def shutdown(self) -> None:
        """Gracefully shutdown the cluster."""
        logger.info(f"Shutting down cluster '{self.name}'")

        # Stop health monitoring
        if self.health_monitor:
            await self.health_monitor.stop()

        # Stop load balancer
        if self.load_balancer:
            await self.load_balancer.stop()

        # Shutdown consensus
        if self.consensus_manager:
            await self.consensus_manager.shutdown()

        # Shutdown all nodes
        for node in self.nodes.values():
            node.status = "shutdown"

        self.is_deployed = False
        logger.info("Cluster shutdown completed")

    def __str__(self) -> str:
        """String representation of cluster."""
        return f"LineageCluster(name={self.name}, nodes={len(self.nodes)}, status={self.get_status().cluster_health})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        status = self.get_status()
        return (
            f"LineageCluster(name='{self.name}', cluster_id='{self.cluster_id}', "
            f"nodes={status.total_nodes}, healthy={status.healthy_nodes}, "
            f"leader='{status.leader_node}', health='{status.cluster_health}')"
        )


class ClusterManager:
    """
    High-level manager for multiple lineage clusters.

    Provides cluster lifecycle management, monitoring, and coordination
    across multiple deployment environments.
    """

    def __init__(self, config: Optional[EnterpriseConfig] = None):
        self.config = config or EnterpriseConfig()
        self.clusters: Dict[str, LineageCluster] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

        logger.info("ClusterManager initialized")

    async def create_cluster(
        self,
        name: str,
        nodes: List[str],
        **kwargs
    ) -> LineageCluster:
        """Create and deploy a new lineage cluster."""
        if name in self.clusters:
            raise ClusterError(f"Cluster '{name}' already exists")

        cluster = LineageCluster(
            name=name,
            nodes=nodes,
            config=self.config.cluster,
            **kwargs
        )

        await cluster.deploy()
        self.clusters[name] = cluster

        logger.info(f"Created cluster '{name}' with {len(nodes)} nodes")
        return cluster

    def get_cluster(self, name: str) -> LineageCluster:
        """Get cluster by name."""
        if name not in self.clusters:
            raise ClusterError(f"Cluster '{name}' not found")
        return self.clusters[name]

    def list_clusters(self) -> List[str]:
        """List all managed clusters."""
        return list(self.clusters.keys())

    def get_cluster_status(self, name: str) -> ClusterStatus:
        """Get status of specific cluster."""
        cluster = self.get_cluster(name)
        return cluster.get_status()

    def get_all_cluster_status(self) -> Dict[str, ClusterStatus]:
        """Get status of all clusters."""
        return {
            name: cluster.get_status()
            for name, cluster in self.clusters.items()
        }

    async def delete_cluster(self, name: str) -> None:
        """Delete a cluster."""
        cluster = self.get_cluster(name)
        await cluster.shutdown()
        del self.clusters[name]

        logger.info(f"Deleted cluster '{name}'")

    async def shutdown_all(self) -> None:
        """Shutdown all managed clusters."""
        for cluster in self.clusters.values():
            await cluster.shutdown()

        self.clusters.clear()
        self.executor.shutdown(wait=True)

        logger.info("All clusters shut down")

    def __str__(self) -> str:
        """String representation of cluster manager."""
        return f"ClusterManager(clusters={len(self.clusters)})"

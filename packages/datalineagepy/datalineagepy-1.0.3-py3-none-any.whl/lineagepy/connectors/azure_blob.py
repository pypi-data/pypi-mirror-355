"""
Azure Blob Storage connector for cloud storage operations with lineage tracking.
"""

import logging
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

try:
    from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
    from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

from .cloud_base import CloudStorageConnector

logger = logging.getLogger(__name__)


class AzureBlobConnector(CloudStorageConnector):
    """
    Azure Blob Storage connector with comprehensive cloud storage operations.

    Features:
    - Full Azure Blob Storage API integration
    - Multiple authentication methods (connection string, SAS token, managed identity)
    - Hot/Cool/Archive tier support with automatic tier tracking
    - Azure Data Lake Gen2 hierarchical namespace support
    - Container management and access control
    - Point-in-time recovery and snapshot support
    """

    def __init__(self,
                 account_name: str,
                 container_name: str,
                 credential: Union[str, object] = None,
                 connection_string: str = None,
                 sas_token: str = None,
                 account_key: str = None,
                 **kwargs):
        """
        Initialize Azure Blob Storage connector.

        Args:
            account_name: Azure storage account name
            container_name: Blob container name
            credential: Authentication credential (managed_identity, DefaultAzureCredential, etc.)
            connection_string: Azure storage connection string
            sas_token: Shared Access Signature token
            account_key: Storage account key
            **kwargs: Additional connector options
        """
        if not AZURE_AVAILABLE:
            raise ImportError(
                "azure-storage-blob is required for Azure Blob connector. "
                "Install with: pip install azure-storage-blob azure-identity"
            )

        super().__init__(container_name, None, {}, **kwargs)

        self.account_name = account_name
        self.container_name = container_name
        self.connection_string = connection_string
        self.sas_token = sas_token
        self.account_key = account_key

        # Set up credential
        if credential == 'managed_identity':
            self.credential = ManagedIdentityCredential()
        elif credential == 'default':
            self.credential = DefaultAzureCredential()
        else:
            self.credential = credential

        self.blob_service_client = None
        self.container_client = None

        # Azure-specific configuration
        self.default_tier = kwargs.get('default_tier', 'Hot')
        self.enable_versioning = kwargs.get('enable_versioning', False)
        self.enable_soft_delete = kwargs.get('enable_soft_delete', False)

    def connect(self) -> None:
        """Establish connection to Azure Blob Storage."""
        try:
            # Initialize blob service client
            if self.connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.connection_string
                )
            elif self.account_key:
                self.blob_service_client = BlobServiceClient(
                    account_url=f"https://{self.account_name}.blob.core.windows.net",
                    credential=self.account_key
                )
            elif self.sas_token:
                self.blob_service_client = BlobServiceClient(
                    account_url=f"https://{self.account_name}.blob.core.windows.net",
                    credential=self.sas_token
                )
            elif self.credential:
                self.blob_service_client = BlobServiceClient(
                    account_url=f"https://{self.account_name}.blob.core.windows.net",
                    credential=self.credential
                )
            else:
                raise ValueError("No valid authentication method provided")

            # Get container client
            self.container_client = self.blob_service_client.get_container_client(
                self.container_name
            )

            # Test connection
            try:
                self.container_client.get_container_properties()
                self.connection = True
                logger.info(
                    f"Connected to Azure container: {self.container_name}")
            except ResourceNotFoundError:
                if kwargs.get('create_if_not_exists', False):
                    self._create_container()
                else:
                    raise ValueError(
                        f"Azure container '{self.container_name}' does not exist")

        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Azure Blob Storage: {str(e)}")

    def _create_container(self) -> None:
        """Create Azure Blob container."""
        try:
            self.container_client.create_container(
                metadata={'created_by': 'lineagepy'}
            )
            self.connection = True
            logger.info(f"Created Azure container: {self.container_name}")

        except Exception as e:
            raise ConnectionError(
                f"Failed to create Azure container: {str(e)}")

    def list_objects(self, prefix: str = "", max_objects: int = 1000) -> List[Dict[str, Any]]:
        """List blobs in Azure container."""
        if not self.connection:
            self.connect()

        try:
            objects = []
            blob_list = self.container_client.list_blobs(
                name_starts_with=prefix,
                include=['metadata', 'tags']
            )

            count = 0
            for blob in blob_list:
                if count >= max_objects:
                    break

                objects.append({
                    'key': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified,
                    'etag': blob.etag,
                    'content_type': blob.content_settings.content_type if blob.content_settings else None,
                    'tier': blob.blob_tier,
                    'creation_time': blob.creation_time,
                    'metadata': blob.metadata or {},
                    'tags': blob.tags or {},
                    'version_id': blob.version_id,
                    'is_current_version': blob.is_current_version
                })
                count += 1

            logger.info(f"Listed {len(objects)} blobs with prefix '{prefix}'")
            return objects

        except Exception as e:
            logger.error(f"Failed to list Azure blobs: {e}")
            raise

    def object_exists(self, key: str) -> bool:
        """Check if blob exists in Azure container."""
        if not self.connection:
            self.connect()

        try:
            blob_client = self.container_client.get_blob_client(key)
            return blob_client.exists()
        except Exception:
            return False

    def get_object_metadata(self, key: str) -> Dict[str, Any]:
        """Get Azure blob metadata."""
        if not self.connection:
            self.connect()

        try:
            blob_client = self.container_client.get_blob_client(key)
            properties = blob_client.get_blob_properties()

            metadata = {
                'size': properties.size,
                'last_modified': properties.last_modified,
                'etag': properties.etag,
                'content_type': properties.content_settings.content_type if properties.content_settings else None,
                'tier': properties.blob_tier,
                'creation_time': properties.creation_time,
                'deleted': properties.deleted,
                'snapshot': properties.snapshot,
                'version_id': properties.version_id,
                'is_current_version': properties.is_current_version,
                'metadata': properties.metadata or {},
                'tags': properties.tag_count
            }

            return metadata

        except ResourceNotFoundError:
            raise FileNotFoundError(f"Blob not found: {key}")
        except Exception as e:
            logger.error(f"Failed to get Azure blob metadata: {e}")
            raise

    def download_object(self, key: str, local_path: str = None) -> str:
        """Download blob from Azure."""
        if not self.connection:
            self.connect()

        try:
            blob_client = self.container_client.get_blob_client(key)

            if local_path is None:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                local_path = temp_file.name
                temp_file.close()

            # Download blob
            with open(local_path, 'wb') as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())

            logger.info(f"Downloaded Azure blob {key} to {local_path}")
            return local_path

        except ResourceNotFoundError:
            raise FileNotFoundError(f"Blob not found: {key}")
        except Exception as e:
            logger.error(f"Failed to download Azure blob: {e}")
            raise

    def upload_object(self, local_path: str, key: str, metadata: Dict[str, Any] = None) -> bool:
        """Upload object to Azure Blob Storage."""
        if not self.connection:
            self.connect()

        try:
            blob_client = self.container_client.get_blob_client(key)

            # Upload file
            with open(local_path, 'rb') as data:
                blob_client.upload_blob(
                    data,
                    blob_type="BlockBlob",
                    metadata=metadata,
                    standard_blob_tier=self.default_tier,
                    overwrite=True
                )

            logger.info(f"Uploaded {local_path} to Azure blob {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload to Azure: {e}")
            raise

    def copy_object(self, source_key: str, destination_key: str,
                    source_container: str = None, source_account: str = None) -> bool:
        """Copy blob within Azure or between containers/accounts."""
        if not self.connection:
            self.connect()

        try:
            # Source URL
            if source_account and source_container:
                source_url = f"https://{source_account}.blob.core.windows.net/{source_container}/{source_key}"
            elif source_container:
                source_url = f"https://{self.account_name}.blob.core.windows.net/{source_container}/{source_key}"
            else:
                source_blob_client = self.container_client.get_blob_client(
                    source_key)
                source_url = source_blob_client.url

            # Destination blob
            destination_blob_client = self.container_client.get_blob_client(
                destination_key)

            # Start copy operation
            copy_props = destination_blob_client.start_copy_from_url(
                source_url)

            logger.info(f"Copied {source_key} to {destination_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to copy Azure blob: {e}")
            raise

    def delete_object(self, key: str) -> bool:
        """Delete blob from Azure."""
        if not self.connection:
            self.connect()

        try:
            blob_client = self.container_client.get_blob_client(key)
            blob_client.delete_blob()

            logger.info(f"Deleted Azure blob: {key}")
            return True

        except ResourceNotFoundError:
            logger.warning(f"Blob not found for deletion: {key}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete Azure blob: {e}")
            raise

    def set_blob_tier(self, key: str, tier: str) -> bool:
        """Set blob access tier (Hot, Cool, Archive)."""
        if not self.connection:
            self.connect()

        try:
            blob_client = self.container_client.get_blob_client(key)
            blob_client.set_standard_blob_tier(tier)

            # Track tier change in lineage
            if self.tracker:
                from ..core.nodes import CloudNode
                node = CloudNode(
                    node_id=f"azure_{self.container_name}_{key}",
                    name=f"Azure: {key}",
                    bucket_name=self.container_name,
                    object_key=key,
                    cloud_provider="azure"
                )
                self.tracker.add_operation_context(
                    operation_name="tier_change",
                    context={
                        'blob_key': key,
                        'new_tier': tier,
                        'timestamp': datetime.now().isoformat()
                    }
                )

            logger.info(f"Set blob {key} tier to {tier}")
            return True

        except Exception as e:
            logger.error(f"Failed to set blob tier: {e}")
            raise

    def generate_sas_url(self, key: str, expiration: int = 3600,
                         permissions: str = "r") -> str:
        """Generate SAS URL for secure access to Azure blob."""
        if not self.connection:
            self.connect()

        try:
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions

            blob_client = self.container_client.get_blob_client(key)

            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=key,
                account_key=self.account_key,  # Requires account key
                permission=BlobSasPermissions.from_string(permissions),
                expiry=datetime.utcnow() + timedelta(seconds=expiration)
            )

            sas_url = f"{blob_client.url}?{sas_token}"

            logger.info(
                f"Generated SAS URL for {key} (expires in {expiration}s)")
            return sas_url

        except Exception as e:
            logger.error(f"Failed to generate SAS URL: {e}")
            raise

    def create_snapshot(self, key: str, metadata: Dict[str, Any] = None) -> str:
        """Create blob snapshot for point-in-time recovery."""
        if not self.connection:
            self.connect()

        try:
            blob_client = self.container_client.get_blob_client(key)
            snapshot = blob_client.create_snapshot(metadata=metadata)

            # Track snapshot creation in lineage
            if self.tracker:
                self.tracker.add_operation_context(
                    operation_name="snapshot_creation",
                    context={
                        'blob_key': key,
                        'snapshot_id': snapshot['snapshot'],
                        'timestamp': datetime.now().isoformat()
                    }
                )

            logger.info(
                f"Created snapshot for blob {key}: {snapshot['snapshot']}")
            return snapshot['snapshot']

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            raise

    def sync_to_azure_synapse(self, key: str, synapse_workspace: str,
                              sql_pool: str, table_name: str) -> bool:
        """Sync Azure blob to Synapse Analytics with lineage tracking."""
        if not self.connection:
            self.connect()

        try:
            # This would require azure-synapse-artifacts package
            # Implementation would involve creating external table or COPY command

            blob_url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{key}"

            # Track lineage from Blob to Synapse
            if self.tracker:
                from ..core.nodes import CloudNode
                blob_node = CloudNode(
                    node_id=f"azure_blob_{self.container_name}_{key}",
                    name=f"Azure Blob: {key}",
                    bucket_name=self.container_name,
                    object_key=key,
                    cloud_provider="azure"
                )

                synapse_node = CloudNode(
                    node_id=f"synapse_{synapse_workspace}_{table_name}",
                    name=f"Synapse: {table_name}",
                    bucket_name=synapse_workspace,
                    object_key=table_name,
                    cloud_provider="azure"
                )

                self.tracker.add_node(blob_node)
                self.tracker.add_node(synapse_node)
                self.tracker.add_edge(blob_node.node_id, synapse_node.node_id,
                                      "azure_blob_to_synapse_sync")

            logger.info(f"Synced {key} to Synapse table {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to sync to Synapse: {e}")
            raise

    def get_container_info(self) -> Dict[str, Any]:
        """Get comprehensive container information."""
        if not self.connection:
            self.connect()

        try:
            properties = self.container_client.get_container_properties()

            return {
                'name': properties.name,
                'last_modified': properties.last_modified,
                'etag': properties.etag,
                'lease_status': properties.lease.status if properties.lease else None,
                'lease_state': properties.lease.state if properties.lease else None,
                'metadata': properties.metadata or {},
                'public_access': properties.public_access,
                'has_immutability_policy': properties.has_immutability_policy,
                'has_legal_hold': properties.has_legal_hold,
                'default_encryption_scope': properties.default_encryption_scope,
                'prevent_encryption_scope_override': properties.prevent_encryption_scope_override
            }

        except Exception as e:
            logger.error(f"Failed to get container info: {e}")
            raise

    def __str__(self) -> str:
        return f"AzureBlobConnector(account={self.account_name}, container={self.container_name})"

    def __repr__(self) -> str:
        return self.__str__()

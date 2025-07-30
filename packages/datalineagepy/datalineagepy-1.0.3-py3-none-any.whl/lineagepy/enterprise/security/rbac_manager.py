"""
Role-Based Access Control (RBAC) Manager

Enterprise-grade RBAC system with fine-grained permissions,
resource-level authorization, and policy enforcement.
"""

import json
import uuid
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

from ..exceptions import SecurityError, AuthenticationError, AuthorizationError
from ..config import SecurityConfig

logger = logging.getLogger(__name__)


class PermissionType(Enum):
    """Types of permissions in the lineage system."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"
    CREATE = "create"
    UPDATE = "update"
    SHARE = "share"


class ResourceType(Enum):
    """Types of resources that can be protected."""
    LINEAGE_GRAPH = "lineage_graph"
    DATASET = "dataset"
    TRANSFORMATION = "transformation"
    SCHEMA = "schema"
    METADATA = "metadata"
    CLUSTER = "cluster"
    TENANT = "tenant"
    USER = "user"
    ROLE = "role"
    POLICY = "policy"
    AUDIT_LOG = "audit_log"


@dataclass
class Permission:
    """Represents a specific permission on a resource."""
    resource_type: ResourceType
    action: PermissionType
    permission_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    resource_id: Optional[str] = None  # None means all resources of this type
    conditions: Dict[str, Any] = field(default_factory=dict)
    granted_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    def matches_request(
        self,
        resource_type: ResourceType,
        resource_id: str,
        action: PermissionType,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if this permission matches an authorization request."""
        # Check resource type
        if self.resource_type != resource_type:
            return False

        # Check resource ID (None means all resources)
        if self.resource_id is not None and self.resource_id != resource_id:
            return False

        # Check action (admin includes all actions)
        if self.action != action and self.action != PermissionType.ADMIN:
            return False

        # Check if permission has expired
        if self.expires_at and datetime.now() > self.expires_at:
            return False

        # Check conditions
        if self.conditions and context:
            for condition_key, condition_value in self.conditions.items():
                if condition_key not in context:
                    return False
                if context[condition_key] != condition_value:
                    return False

        return True

    def is_expired(self) -> bool:
        """Check if permission has expired."""
        return self.expires_at is not None and datetime.now() > self.expires_at


@dataclass
class Role:
    """Represents a role with associated permissions."""
    name: str
    role_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    permissions: Set[Permission] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_system_role: bool = False

    def add_permission(self, permission: Permission) -> None:
        """Add a permission to this role."""
        self.permissions.add(permission)
        self.updated_at = datetime.now()

    def remove_permission(self, permission_id: str) -> bool:
        """Remove a permission from this role."""
        for perm in self.permissions:
            if perm.permission_id == permission_id:
                self.permissions.remove(perm)
                self.updated_at = datetime.now()
                return True
        return False

    def has_permission(
        self,
        resource_type: ResourceType,
        resource_id: str,
        action: PermissionType,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if role has specific permission."""
        for permission in self.permissions:
            if permission.matches_request(resource_type, resource_id, action, context):
                return True
        return False

    def cleanup_expired_permissions(self) -> int:
        """Remove expired permissions and return count removed."""
        expired_perms = {p for p in self.permissions if p.is_expired()}
        self.permissions -= expired_perms
        if expired_perms:
            self.updated_at = datetime.now()
        return len(expired_perms)


@dataclass
class User:
    """Represents a user in the RBAC system."""
    username: str
    email: str
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    display_name: str = ""
    roles: Set[str] = field(default_factory=set)  # Role IDs
    tenant_id: Optional[str] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_role(self, role_id: str) -> None:
        """Add a role to this user."""
        self.roles.add(role_id)

    def remove_role(self, role_id: str) -> bool:
        """Remove a role from this user."""
        if role_id in self.roles:
            self.roles.remove(role_id)
            return True
        return False

    def has_role(self, role_id: str) -> bool:
        """Check if user has specific role."""
        return role_id in self.roles


@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    name: str
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    rules: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate policy against given context."""
        # Simple rule evaluation - extend for complex policies
        for rule_name, rule_config in self.rules.items():
            if not self._evaluate_rule(rule_name, rule_config, context):
                return False
        return True

    def _evaluate_rule(
        self,
        rule_name: str,
        rule_config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate a single rule."""
        rule_type = rule_config.get('type', 'equals')
        field = rule_config.get('field')
        expected_value = rule_config.get('value')

        if field not in context:
            return rule_config.get('default', False)

        actual_value = context[field]

        if rule_type == 'equals':
            return actual_value == expected_value
        elif rule_type == 'in':
            return actual_value in expected_value
        elif rule_type == 'not_in':
            return actual_value not in expected_value
        elif rule_type == 'regex':
            import re
            return bool(re.match(expected_value, str(actual_value)))
        else:
            logger.warning(f"Unknown rule type: {rule_type}")
            return False


class RBACManager:
    """
    Enterprise Role-Based Access Control Manager.

    Provides comprehensive RBAC functionality including:
    - User and role management
    - Fine-grained permissions
    - Resource-level authorization
    - Policy enforcement
    - Audit integration
    """

    def __init__(
        self,
        auth_provider: str = "internal",
        mfa_required: bool = False,
        config: Optional[SecurityConfig] = None
    ):
        self.auth_provider = auth_provider
        self.mfa_required = mfa_required
        self.config = config or SecurityConfig()

        # Storage for RBAC entities
        self.users: Dict[str, User] = {}
        self.roles: Dict[str, Role] = {}
        self.policies: Dict[str, SecurityPolicy] = {}

        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # Initialize system roles
        self._create_system_roles()

        logger.info(
            f"RBACManager initialized with auth provider: {auth_provider}")

    def _create_system_roles(self) -> None:
        """Create default system roles."""
        system_roles = [
            {
                'name': 'super_admin',
                'description': 'Full system administrator with all permissions',
                'permissions': [
                    Permission(ResourceType.CLUSTER, None,
                               PermissionType.ADMIN),
                    Permission(ResourceType.TENANT, None,
                               PermissionType.ADMIN),
                    Permission(ResourceType.USER, None, PermissionType.ADMIN),
                    Permission(ResourceType.ROLE, None, PermissionType.ADMIN),
                    Permission(ResourceType.POLICY, None,
                               PermissionType.ADMIN),
                ]
            },
            {
                'name': 'tenant_admin',
                'description': 'Tenant administrator with tenant-scoped permissions',
                'permissions': [
                    Permission(ResourceType.LINEAGE_GRAPH,
                               None, PermissionType.ADMIN),
                    Permission(ResourceType.DATASET, None,
                               PermissionType.ADMIN),
                    Permission(ResourceType.TRANSFORMATION,
                               None, PermissionType.ADMIN),
                    Permission(ResourceType.USER, None, PermissionType.READ),
                ]
            },
            {
                'name': 'data_engineer',
                'description': 'Data engineer with lineage creation and modification rights',
                'permissions': [
                    Permission(ResourceType.LINEAGE_GRAPH,
                               None, PermissionType.READ),
                    Permission(ResourceType.LINEAGE_GRAPH,
                               None, PermissionType.WRITE),
                    Permission(ResourceType.DATASET,
                               None, PermissionType.READ),
                    Permission(ResourceType.DATASET, None,
                               PermissionType.WRITE),
                    Permission(ResourceType.TRANSFORMATION,
                               None, PermissionType.READ),
                    Permission(ResourceType.TRANSFORMATION,
                               None, PermissionType.WRITE),
                    Permission(ResourceType.METADATA,
                               None, PermissionType.READ),
                    Permission(ResourceType.METADATA,
                               None, PermissionType.WRITE),
                ]
            },
            {
                'name': 'data_analyst',
                'description': 'Data analyst with read-only access to lineage data',
                'permissions': [
                    Permission(ResourceType.LINEAGE_GRAPH,
                               None, PermissionType.READ),
                    Permission(ResourceType.DATASET,
                               None, PermissionType.READ),
                    Permission(ResourceType.TRANSFORMATION,
                               None, PermissionType.READ),
                    Permission(ResourceType.METADATA,
                               None, PermissionType.READ),
                ]
            },
            {
                'name': 'viewer',
                'description': 'Basic viewer with minimal read permissions',
                'permissions': [
                    Permission(ResourceType.LINEAGE_GRAPH,
                               None, PermissionType.READ),
                ]
            }
        ]

        for role_data in system_roles:
            role = Role(
                name=role_data['name'],
                description=role_data['description'],
                is_system_role=True
            )

            for permission in role_data['permissions']:
                role.add_permission(permission)

            self.roles[role.role_id] = role
            logger.debug(f"Created system role: {role.name}")

    def create_user(
        self,
        username: str,
        email: str,
        display_name: str = "",
        tenant_id: Optional[str] = None,
        initial_roles: Optional[List[str]] = None
    ) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = self.get_user_by_username(username)
        if existing_user:
            raise SecurityError(f"User '{username}' already exists")

        user = User(
            username=username,
            email=email,
            display_name=display_name or username,
            tenant_id=tenant_id
        )

        # Add initial roles
        if initial_roles:
            for role_name in initial_roles:
                role = self.get_role_by_name(role_name)
                if role:
                    user.add_role(role.role_id)

        self.users[user.user_id] = user
        logger.info(f"Created user: {username}")

        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def create_role(
        self,
        name: str,
        description: str = "",
        permissions: Optional[List[Permission]] = None
    ) -> Role:
        """Create a new role."""
        # Check if role already exists
        existing_role = self.get_role_by_name(name)
        if existing_role:
            raise SecurityError(f"Role '{name}' already exists")

        role = Role(name=name, description=description)

        if permissions:
            for permission in permissions:
                role.add_permission(permission)

        self.roles[role.role_id] = role
        logger.info(f"Created role: {name}")

        return role

    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        for role in self.roles.values():
            if role.name == name:
                return role
        return None

    def assign_role_to_user(self, username: str, role_name: str) -> bool:
        """Assign a role to a user."""
        user = self.get_user_by_username(username)
        if not user:
            raise SecurityError(f"User '{username}' not found")

        role = self.get_role_by_name(role_name)
        if not role:
            raise SecurityError(f"Role '{role_name}' not found")

        user.add_role(role.role_id)
        logger.info(f"Assigned role '{role_name}' to user '{username}'")

        return True

    def revoke_role_from_user(self, username: str, role_name: str) -> bool:
        """Revoke a role from a user."""
        user = self.get_user_by_username(username)
        if not user:
            raise SecurityError(f"User '{username}' not found")

        role = self.get_role_by_name(role_name)
        if not role:
            raise SecurityError(f"Role '{role_name}' not found")

        result = user.remove_role(role.role_id)
        if result:
            logger.info(f"Revoked role '{role_name}' from user '{username}'")

        return result

    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """Authenticate a user and return session token."""
        user = self.get_user_by_username(username)
        if not user or not user.is_active:
            raise AuthenticationError(
                f"Authentication failed for user: {username}")

        # In real implementation, verify password against auth provider
        # For now, simulate successful authentication

        # Create session
        session_token = str(uuid.uuid4())
        session_data = {
            'user_id': user.user_id,
            'username': username,
            'tenant_id': user.tenant_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=self.config.session_timeout_minutes)
        }

        self.active_sessions[session_token] = session_data
        user.last_login = datetime.now()

        logger.info(f"User '{username}' authenticated successfully")
        return True, session_token

    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate a session token."""
        if session_token not in self.active_sessions:
            return None

        session = self.active_sessions[session_token]
        if datetime.now() > session['expires_at']:
            del self.active_sessions[session_token]
            return None

        return session

    def authorize(
        self,
        user: str,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Authorize a user action on a resource.

        Args:
            user: Username or user ID
            action: Action to perform (read, write, delete, etc.)
            resource: Resource identifier (format: type/id)
            context: Additional context for authorization

        Returns:
            True if authorized, False otherwise
        """
        try:
            # Get user
            user_obj = self.get_user_by_username(user)
            if not user_obj:
                user_obj = self.users.get(user)

            if not user_obj or not user_obj.is_active:
                raise AuthorizationError(f"User not found or inactive: {user}")

            # Parse resource
            if '/' in resource:
                resource_type_str, resource_id = resource.split('/', 1)
            else:
                resource_type_str = resource
                resource_id = "*"

            try:
                resource_type = ResourceType(resource_type_str)
            except ValueError:
                logger.warning(f"Unknown resource type: {resource_type_str}")
                return False

            try:
                action_type = PermissionType(action)
            except ValueError:
                logger.warning(f"Unknown action type: {action}")
                return False

            # Add tenant context if available
            if context is None:
                context = {}
            if user_obj.tenant_id:
                context['tenant_id'] = user_obj.tenant_id

            # Check permissions through user roles
            for role_id in user_obj.roles:
                if role_id in self.roles:
                    role = self.roles[role_id]
                    if role.has_permission(resource_type, resource_id, action_type, context):
                        logger.debug(
                            f"Authorization granted for {user} on {resource} via role {role.name}")
                        return True

            logger.debug(f"Authorization denied for {user} on {resource}")
            return False

        except Exception as e:
            logger.error(f"Authorization error: {e}")
            raise AuthorizationError(f"Authorization failed: {e}")

    def create_policy(
        self,
        name: str,
        description: str = "",
        rules: Optional[Dict[str, Any]] = None
    ) -> SecurityPolicy:
        """Create a security policy."""
        policy = SecurityPolicy(
            name=name,
            description=description,
            rules=rules or {}
        )

        self.policies[policy.policy_id] = policy
        logger.info(f"Created security policy: {name}")

        return policy

    def evaluate_policies(self, context: Dict[str, Any]) -> bool:
        """Evaluate all active policies against given context."""
        for policy in self.policies.values():
            if policy.is_active and not policy.evaluate(context):
                logger.warning(f"Policy violation: {policy.name}")
                return False
        return True

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count removed."""
        now = datetime.now()
        expired_sessions = [
            token for token, session in self.active_sessions.items()
            if now > session['expires_at']
        ]

        for token in expired_sessions:
            del self.active_sessions[token]

        return len(expired_sessions)

    def cleanup_expired_permissions(self) -> int:
        """Remove expired permissions from all roles."""
        total_cleaned = 0
        for role in self.roles.values():
            total_cleaned += role.cleanup_expired_permissions()
        return total_cleaned

    def get_user_permissions(self, username: str) -> List[Permission]:
        """Get all permissions for a user."""
        user = self.get_user_by_username(username)
        if not user:
            return []

        permissions = []
        for role_id in user.roles:
            if role_id in self.roles:
                role = self.roles[role_id]
                permissions.extend(role.permissions)

        return permissions

    def export_rbac_config(self) -> Dict[str, Any]:
        """Export RBAC configuration to dictionary."""
        return {
            'users': {
                user_id: {
                    'username': user.username,
                    'email': user.email,
                    'display_name': user.display_name,
                    'roles': list(user.roles),
                    'tenant_id': user.tenant_id,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat()
                }
                for user_id, user in self.users.items()
            },
            'roles': {
                role_id: {
                    'name': role.name,
                    'description': role.description,
                    'is_system_role': role.is_system_role,
                    'permissions': [
                        {
                            'resource_type': perm.resource_type.value,
                            'resource_id': perm.resource_id,
                            'action': perm.action.value,
                            'conditions': perm.conditions
                        }
                        for perm in role.permissions
                    ]
                }
                for role_id, role in self.roles.items()
            },
            'policies': {
                policy_id: {
                    'name': policy.name,
                    'description': policy.description,
                    'rules': policy.rules,
                    'is_active': policy.is_active
                }
                for policy_id, policy in self.policies.items()
            }
        }

    def import_rbac_config(self, config_data: Dict[str, Any]) -> None:
        """Import RBAC configuration from dictionary."""
        # Import roles first
        for role_data in config_data.get('roles', {}).values():
            if not self.get_role_by_name(role_data['name']):
                role = Role(
                    name=role_data['name'],
                    description=role_data['description'],
                    is_system_role=role_data.get('is_system_role', False)
                )

                for perm_data in role_data.get('permissions', []):
                    permission = Permission(
                        resource_type=ResourceType(perm_data['resource_type']),
                        resource_id=perm_data.get('resource_id'),
                        action=PermissionType(perm_data['action']),
                        conditions=perm_data.get('conditions', {})
                    )
                    role.add_permission(permission)

                self.roles[role.role_id] = role

        # Import users
        for user_data in config_data.get('users', {}).values():
            if not self.get_user_by_username(user_data['username']):
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    display_name=user_data['display_name'],
                    tenant_id=user_data.get('tenant_id'),
                    is_active=user_data.get('is_active', True)
                )

                # Assign roles by name
                for role_name in user_data.get('role_names', []):
                    role = self.get_role_by_name(role_name)
                    if role:
                        user.add_role(role.role_id)

                self.users[user.user_id] = user

        # Import policies
        for policy_data in config_data.get('policies', {}).values():
            policy = SecurityPolicy(
                name=policy_data['name'],
                description=policy_data['description'],
                rules=policy_data.get('rules', {}),
                is_active=policy_data.get('is_active', True)
            )
            self.policies[policy.policy_id] = policy

        logger.info("RBAC configuration imported successfully")

    def __str__(self) -> str:
        """String representation of RBAC manager."""
        return f"RBACManager(users={len(self.users)}, roles={len(self.roles)}, policies={len(self.policies)})"

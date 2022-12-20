from .core.application import (
    ApplicationCreatedAuditLogType,
    ApplicationDeletedAuditLogType,
    ApplicationReorderedAuditLogType,
    ApplicationUpdatedAuditLogType,
)
from .core.group import (
    GroupCreatedAuditLogType,
    GroupDeletedAuditLogType,
    GroupUpdatedAuditLogType,
    GroupReorderedAuditLogType,
    GroupRestoredAuditLogType,
    GroupUserAddedAuditLogType,
    GroupUserDeletedAuditLogType,
)

from .core.user import (
    UserCreatedAuditLogType,
    UserDeletedAuditLogType,
    UserRestoredAuditLogType,
    UserPermanentlyDeletedAuditLogType,
)


from baserow_enterprise.registries import audit_log_type_registry


def register_audit_log_types():
    audit_log_type_registry.register(ApplicationCreatedAuditLogType())
    audit_log_type_registry.register(ApplicationDeletedAuditLogType())
    audit_log_type_registry.register(ApplicationReorderedAuditLogType())
    audit_log_type_registry.register(ApplicationUpdatedAuditLogType())

    audit_log_type_registry.register(GroupCreatedAuditLogType())
    audit_log_type_registry.register(GroupDeletedAuditLogType())
    audit_log_type_registry.register(GroupUpdatedAuditLogType())
    audit_log_type_registry.register(GroupReorderedAuditLogType())
    audit_log_type_registry.register(GroupRestoredAuditLogType())
    audit_log_type_registry.register(GroupUserAddedAuditLogType())
    audit_log_type_registry.register(GroupUserDeletedAuditLogType())

    audit_log_type_registry.register(UserCreatedAuditLogType())
    audit_log_type_registry.register(UserDeletedAuditLogType())
    audit_log_type_registry.register(UserRestoredAuditLogType())
    audit_log_type_registry.register(UserPermanentlyDeletedAuditLogType())

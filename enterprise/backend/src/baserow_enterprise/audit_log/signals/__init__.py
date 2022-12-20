from .core.application import (
    ApplicationCreatedAuditLogType,
    ApplicationDeletedAuditLogType,
    ApplicationUpdatedAuditLogType,
)
from .core.group import (
    GroupCreatedAuditLogType,
    GroupDeletedAuditLogType,
    GroupUpdatedAuditLogType,
)


from baserow_enterprise.registries import audit_log_type_registry


def register_audit_log_types():
    audit_log_type_registry.register(ApplicationCreatedAuditLogType())
    audit_log_type_registry.register(ApplicationDeletedAuditLogType())
    audit_log_type_registry.register(ApplicationUpdatedAuditLogType())

    audit_log_type_registry.register(GroupCreatedAuditLogType())
    audit_log_type_registry.register(GroupDeletedAuditLogType())
    audit_log_type_registry.register(GroupUpdatedAuditLogType())

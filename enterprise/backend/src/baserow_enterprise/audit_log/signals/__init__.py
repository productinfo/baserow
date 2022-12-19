from .core.group import (
    GroupCreatedAuditLogType,
    GroupUpdatedAuditLogType,
    GroupDeletedAuditLogType,
)


from baserow_enterprise.registries import audit_log_type_registry


def register_audit_log_types():
    audit_log_type_registry.register(GroupCreatedAuditLogType())
    audit_log_type_registry.register(GroupUpdatedAuditLogType())
    audit_log_type_registry.register(GroupDeletedAuditLogType())

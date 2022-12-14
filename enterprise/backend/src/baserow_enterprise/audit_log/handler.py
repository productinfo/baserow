from .models import AuditLog


class AuditLogHandler:
    @classmethod
    def register_auditable_event(cls, auditable_event):
        """ """

        audit_log_entries = []
        for target in action_context.target:
            audit_log_entry = AuditLog(
                user=action_context.user,
                group=action_context.group,
                action=action_context.action,
                context=action_context.context,
                target=target,
                timestamp=action_context.timestamp,
                from_state=action_context.from_state,
                to_state=action_context.to_state,
            )
            audit_log_entry.populate_reprs()
            audit_log_entries.append(audit_log_entry)

        AuditLogHandler.bulk_create(audit_log_entries)

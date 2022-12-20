from django.db import models

from baserow_enterprise.registries import audit_log_type_registry


class AuditLogEntry(models.Model):
    event_type = models.CharField(max_length=32, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    ip_address = models.GenericIPAddressField(null=True)

    user_id = models.PositiveIntegerField(db_index=True, null=True)
    user_email = models.CharField(max_length=150, db_index=True, null=True, blank=True)

    group_id = models.PositiveIntegerField(db_index=True, null=True)
    group_name = models.CharField(max_length=160, db_index=True, null=True, blank=True)

    data = models.JSONField(null=True)

    def get_type_description(self):
        event_type = audit_log_type_registry.get(self.event_type)
        return event_type.get_type_description(self)

    def get_event_description(self):
        event_type = audit_log_type_registry.get(self.event_type)
        return event_type.get_event_description(self)

    class Meta:
        ordering = ["-timestamp"]

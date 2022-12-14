from dataclasses import asdict

from .models import AuditLog


class AuditLogHandler:
    @classmethod
    def register_event(cls, event):
        """ """

        AuditLog.objects.create(**asdict(event))

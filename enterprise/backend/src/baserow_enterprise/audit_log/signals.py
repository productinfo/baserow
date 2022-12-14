from django.dispatch import receiver

from baserow.core.signals import auditable_event
from baserow_enterprise.audit_log.handler import AuditLogHandler


@receiver(auditable_event)
def action_registered_handler(sender, event, **kwargs):
    """
    When an action is registered this handler will register the action with the
    action handler.
    """

    AuditLogHandler.register_event(event)

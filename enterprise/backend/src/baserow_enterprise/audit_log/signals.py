from django.dispatch import receiver

from baserow.core.action.signals import action_registered
from baserow_enterprise.audit_log.handler import AuditLogHandler


@receiver(action_registered)
def action_registered_handler(sender, action, context, **kwargs):
    """
    When an action is registered this handler will register the action with the
    action handler.
    """

    AuditLogHandler.register_action_log_entry(context)

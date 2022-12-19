from django.utils.translation import gettext as _

from baserow.core import signals
from baserow_enterprise.registries import AuditLogType
from baserow_enterprise.audit_log.handler import AuditLogHandler


class GroupCreatedAuditLogType(AuditLogType):
    type = "group_created"
    signal = signals.group_created

    def receiver(self, sender, group, user, **kwargs):
        AuditLogHandler.log_event(
            user=user,
            group=group,
            event_type=self.type,
            data={"name": group.name},
        )

    def get_type_description(self):
        return _("Group created")

    def get_event_description(self, audit_log_entry) -> str:
        return _(
            '%(user_email)s created the group "%(group_name)s" (%(group_id)s).'
        ) % {
            "user_email": audit_log_entry.user_email,
            "group_name": audit_log_entry.group_name,
            "group_id": audit_log_entry.group_id,
        }


class GroupUpdatedAuditLogType(AuditLogType):
    type = "group_updated"
    signal = signals.group_updated

    def receiver(self, sender, group, user, before_update, **kwargs):
        data = AuditLogHandler.get_data_diff(before_update, group)
        AuditLogHandler.log_event(
            user=user,
            group=group,
            event_type=self.type,
            data=data,
        )

    def get_type_description(self):
        return _("Group updated")

    def get_event_description(self, audit_log_entry) -> str:
        return _(
            '%(user_email)s updated the group\'s name from "%(from_name)s"'
            ' to "%(to_name)s" (%(group_id)s).'
        ) % {
            "user_email": audit_log_entry.user_email,
            "group_id": audit_log_entry.group_id,
            "from_name": audit_log_entry.data["from"]["name"],
            "to_name": audit_log_entry.data["to"]["name"],
        }


class GroupDeletedAuditLogType(AuditLogType):
    type = "group_deleted"
    signal = signals.group_deleted

    def receiver(self, sender, group, group_users, user, **kwargs):
        AuditLogHandler.log_event(
            user=user,
            group=group,
            event_type=self.type,
            data={"name": group.name},
        )

    def get_type_description(self):
        return _("Group deleted")

    def get_event_description(self, audit_log_entry) -> str:
        return _(
            '%(user_email)s deleted the group "%(group_name)s" (%(group_id)s).'
        ) % {
            "user_email": audit_log_entry.user_email,
            "group_name": audit_log_entry.group_name,
            "group_id": audit_log_entry.group_id,
        }

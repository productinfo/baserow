from django.utils.translation import gettext as _

from baserow.core import signals
from baserow_enterprise.registries import AuditLogType
from baserow_enterprise.audit_log.handler import AuditLogHandler


# @ TODO: Add receivers for the following signals.
# group_user_updated = Signal()


class GroupCreatedAuditLogType(AuditLogType):
    type = "group_created"
    signal = signals.group_created

    def receiver(self, sender, group, user, **kwargs):
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=group,
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("Group created")

    def get_event_description(self, audit_log_entry) -> str:
        return _('Group "%(group_name)s" created.') % {
            "group_name": audit_log_entry.group_name
        }


class GroupUpdatedAuditLogType(AuditLogType):
    type = "group_updated"
    signal = signals.group_updated

    def receiver(self, sender, group, user, before_update, **kwargs):
        data = AuditLogHandler.get_data_diff(before_update, group)
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=group,
            data=data,
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("Group updated")

    def get_event_description(self, audit_log_entry) -> str:
        return _('Group\'s name from "%(from_name)s" to "%(to_name)s".') % {
            "from_name": audit_log_entry.data["from"]["name"],
            "to_name": audit_log_entry.data["to"]["name"],
        }


class GroupDeletedAuditLogType(AuditLogType):
    type = "group_deleted"
    signal = signals.group_deleted

    def receiver(self, sender, group, group_users, user, **kwargs):
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=group,
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("Group deleted")

    def get_event_description(self, audit_log_entry) -> str:
        return _('Group "%(group_name)s" deleted.') % {
            "group_name": audit_log_entry.group_name,
        }


class GroupRestoredAuditLogType(AuditLogType):
    type = "group_restored"
    signal = signals.group_restored

    def receiver(self, sender, group, group_users, user, **kwargs):
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=group,
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("Group restored")

    def get_event_description(self, audit_log_entry) -> str:
        return _('Group "%(group_name)s" restored.') % {
            "group_name": audit_log_entry.group_name,
        }


class GroupUserAddedAuditLogType(AuditLogType):
    type = "group_user_added"
    signal = signals.group_user_added

    def receiver(self, sender, group_user_id, group_user, user, invitation, **kwargs):
        group = group_user.group
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=group,
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("Group user added")

    def get_event_description(self, audit_log_entry) -> str:
        return _(
            '%(user_email)s has been added to the group "%(group_name)s" via invitation.'
        ) % {
            "user_email": audit_log_entry.user_email,
            "group_name": audit_log_entry.group_name,
        }


class GroupUserDeletedAuditLogType(AuditLogType):
    type = "group_user_deleted"
    signal = signals.group_user_deleted

    def receiver(self, sender, group_user_id, group_user, user, **kwargs):
        group = group_user.group
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=group,
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("Group user deleted")

    def get_event_description(self, audit_log_entry) -> str:
        return _('%(user_email)s has been deleted from the group "%(group_name)s".') % {
            "user_email": audit_log_entry.user_email,
            "group_name": audit_log_entry.group_name,
        }


class GroupReorderedAuditLogType(AuditLogType):
    type = "groups_reordered"
    signal = signals.groups_reordered

    def receiver(self, sender, user, group_ids, **kwargs):

        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            data={"group_ids": group_ids},
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("Groups reordered")

    def get_event_description(self, audit_log_entry) -> str:
        return _("Groups has been reordered.")

from django.utils.translation import gettext as _

from baserow.core import signals
from baserow.core.registries import auth_provider_type_registry
from baserow_enterprise.registries import AuditLogType
from baserow_enterprise.audit_log.handler import AuditLogHandler

# TODO: add these signals
# user_updated = Signal()


class UserCreatedAuditLogType(AuditLogType):
    type = "user_created"
    signal = signals.user_created

    def receiver(self, sender, group, auth_provider, user, **kwargs):
        auth_provider_type = auth_provider_type_registry.get_by_model(auth_provider)
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=group,
            data={
                "auth_provider_id": auth_provider.id,
                "auth_provider_type": auth_provider_type.type,
            },
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("User created")

    def get_event_description(self, audit_log_entry) -> str:
        return _(
            '%(user_email)s has been created and added to the group "%(group_name)s".'
        ) % {
            "user_email": audit_log_entry.user_email,
            "group_name": audit_log_entry.group_name,
            "group_id": audit_log_entry.group_id,
        }


class UserDeletedAuditLogType(AuditLogType):
    type = "user_deleted"
    signal = signals.user_deleted

    def receiver(self, sender, performed_by, user, **kwargs):
        AuditLogHandler.log_event(
            event_type=self.type,
            user=performed_by,
            data={
                "deleted_user_id": user.id,
                "deleted_user_email": user.email,
            },
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("User scheduled for deletion")

    def get_event_description(self, audit_log_entry) -> str:
        return _("%(user_email)s %(user_id)s has been scheduled for deletion.") % {
            "user_id": audit_log_entry.data["deleted_user_id"],
            "user_email": audit_log_entry.data["deleted_user_email"],
        }


class UserRestoredAuditLogType(AuditLogType):
    type = "user_restored"
    signal = signals.user_restored

    def receiver(self, sender, performed_by, user, **kwargs):
        AuditLogHandler.log_event(
            event_type=self.type,
            user=performed_by,
            data={
                "restored_user_id": user.id,
                "restored_user_email": user.email,
            },
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("User deletion cancelled")

    def get_event_description(self, audit_log_entry) -> str:
        return _("%(user_email)s (%(user_id)s) cancelled the scheduled deletion.") % {
            "user_id": audit_log_entry.data["deleted_user_id"],
            "user_email": audit_log_entry.data["deleted_user_email"],
        }


class UserPermanentlyDeletedAuditLogType(AuditLogType):
    type = "user_permanently_deleted"
    signal = signals.user_permanently_deleted

    def receiver(self, sender, user_id, group_ids, user_email, **kwargs):
        AuditLogHandler.log_event(
            event_type=self.type,
            data={
                "user_id": user_id,
                "user_email": user_email,
                "group_ids": group_ids,
            },
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("User deletion cancelled")

    def get_event_description(self, audit_log_entry) -> str:
        return _("%(user_email)s (%(user_id)s) has been permanently deleted.") % {
            "user_id": audit_log_entry.data["user_id"],
            "user_email": audit_log_entry.data["user_email"],
        }

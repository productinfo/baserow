from typing import List
from django.utils.translation import gettext as _

from baserow.core import signals
from baserow_enterprise.registries import AuditLogType
from baserow_enterprise.audit_log.handler import AuditLogHandler


class ApplicationCreatedAuditLogType(AuditLogType):
    type = "application_created"
    signal = signals.application_created

    def receiver(self, sender, application, user, **kwargs):
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=application.group,
            data={
                "id": application.id,
                "name": application.name,
                "type": application.specific_class.__name__,
            },
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("%(app_type)s created") % {
            "app_type": audit_log_entry.data["type"],
        }

    def get_event_description(self, audit_log_entry) -> str:
        return _(
            '%(user_email)s created the %(app_type)s "%(app_name)s" (%(app_id)s).'
        ) % {
            "user_email": audit_log_entry.user_email,
            "app_type": audit_log_entry.data["type"],
            "app_name": audit_log_entry.data["name"],
            "app_id": audit_log_entry.data["id"],
        }


class ApplicationDeletedAuditLogType(AuditLogType):
    type = "application_deleted"
    signal = signals.application_deleted

    def receiver(self, sender, application, user, **kwargs):
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=application.group,
            data={
                "id": application.id,
                "name": application.name,
                "type": application.specific_class.__name__,
            },
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("%(app_type)s deleted") % {
            "app_type": audit_log_entry.data["type"],
        }

    def get_event_description(self, audit_log_entry) -> str:
        return _(
            '%(user_email)s deleted the %(app_type)s "%(app_name)s" (%(app_id)s).'
        ) % {
            "user_email": audit_log_entry.user_email,
            "app_type": audit_log_entry.data["type"],
            "app_name": audit_log_entry.data["name"],
            "app_id": audit_log_entry.data["id"],
        }


class ApplicationUpdatedAuditLogType(AuditLogType):
    type = "application_updated"
    signal = signals.application_updated

    def receiver(self, sender, application, user, before_update, **kwargs):
        diff = AuditLogHandler.get_data_diff(before_update, application)
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=application.group,
            data={
                "id": application.id,
                "type": application.specific_class.__name__,
                **diff,
            },
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("%(app_type)s updated") % {
            "app_type": audit_log_entry.data["type"],
        }

    def get_event_description(self, audit_log_entry) -> str:
        return _(
            '%(user_email)s updated the %(app_type)s from name "%(from_name)s" to name "%(to_name)s" (%(app_id)s).'
        ) % {
            "user_email": audit_log_entry.user_email,
            "app_type": audit_log_entry.data["type"],
            "from_name": audit_log_entry.data["from"]["name"],
            "to_name": audit_log_entry.data["to"]["name"],
            "app_id": audit_log_entry.data["id"],
        }


class ApplicationReorderedAuditLogType(AuditLogType):
    type = "applications_reordered"
    signal = signals.applications_reordered

    def receiver(self, sender, group, order: List[int], user, **kwargs):
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=group,
            data={"order": order},
        )

    def get_type_description(self, audit_log_entry) -> str:
        return _("Applications reordered")

    def get_event_description(self, audit_log_entry) -> str:
        return _(
            "%(user_email)s reordered application with ids order %(order)s in group."
        ) % {
            "user_email": audit_log_entry.user_email,
            "group_id": audit_log_entry.group_id,
            "group_name": audit_log_entry.group_name,
            "order": audit_log_entry.data["order"],
        }

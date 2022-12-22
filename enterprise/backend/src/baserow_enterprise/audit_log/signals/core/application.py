from typing import List
from django.utils.translation import gettext as _

from baserow.core import signals
from baserow_enterprise.registries import AuditLogType
from baserow_enterprise.audit_log.handler import AuditLogHandler


better_translations = {
    "field_updated": _("%(actor)s Field updated"),
}


class ApplicationCreatedAuditLogType(AuditLogType):
    type = "application_created"
    signal = signals.application_created

    def receiver(self, sender, application, user, duplicate_of=None, **kwargs):
        data = {
            "id": application.id,
            "name": application.name,
            "type": application.specific_class.__name__,
        }
        if duplicate_of is not None:
            data["duplicate_of"] = {
                "id": duplicate_of.id,
                "name": duplicate_of.name,
            }
        AuditLogHandler.log_event(
            event_type=self.type,
            user=user,
            group=application.group,
            data=data,
        )

    def get_type_description(self, audit_log_entry) -> str:
        app_type = audit_log_entry.data["type"]
        if audit_log_entry.data.get("duplicate_of"):
            return _("%(app_type)s duplicated") % {"app_type": app_type}
        return _("%(app_type)s created") % {"app_type": app_type}

    def get_event_description(self, audit_log_entry) -> str:
        params = {
            "app_type": audit_log_entry.data["type"],
            "app_name": audit_log_entry.data["name"],
            "app_id": audit_log_entry.data["id"],
        }
        if audit_log_entry.data.get("duplicate_of"):
            duplicate_of = audit_log_entry.data["duplicate_of"]
            params["duplicate_of_app_id"] = duplicate_of["id"]
            params["duplicate_of_app_name"] = duplicate_of["name"]
            return (
                _(
                    '%(app_type)s "%(app_name)s" (%(app_id)s) duplicated from '
                    "%(duplicate_of_app_name)s (%(duplicate_of_app_id)s)."
                )
                % params
            )
        return _('%(app_type)s "%(app_name)s" created.') % params


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
        return _("%(app_type)s deleted") % {"app_type": audit_log_entry.data["type"]}

    def get_event_description(self, audit_log_entry) -> str:
        return _('%(app_type)s "%(app_name)s" (%(app_id)s) deleted.') % {
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
        return _("%(app_type)s updated") % {"app_type": audit_log_entry.data["type"]}

    def get_event_description(self, audit_log_entry) -> str:
        return _(
            '%(app_type)s\'s name changed from "%(from_name)s" to "%(to_name)s" (%(app_id)s).'
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
        return _("Applications has been reordered.")

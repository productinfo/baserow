from typing import Any, Dict

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from baserow.core.models import Group
from .models import AuditLogEntry


class AuditLogHandler:
    @classmethod
    def log_event(
        cls,
        user: AbstractUser,
        group: Group,
        event_type: str,
        data: Dict[str, Any],
    ):
        """
        Creates a new audit log entry for the given user, group and event type. The
        kwargs will be stored as JSON in the data field of the audit log entry.

        :param user: The user that triggered the event.
        :param group: The group that the event was triggered on.
        :param event_type: The type of event that was triggered.
        :param kwargs: The data that should be stored in the data field of the audit log
            entry.
        """

        AuditLogEntry.objects.create(
            event_type=event_type,
            timestamp=timezone.now(),
            user_id=user.id,
            user_email=user.email,
            group_id=group.id,
            group_name=group.name,
            data=data,
        )

    @classmethod
    def get_data_diff(
        cls, before: Dict[str, Any], after: models.Model
    ) -> Dict[str, Any]:
        """
        Returns a dictionary with the difference between the before and after data.

        :param before: The data before the change.
        :param after: The data after the change.
        :return: A dictionary with the difference between the before and after data.
        """

        to_values: Dict[str, Any] = {}
        diff = {"from": before, "to": to_values}

        for key in before:
            to_values[key] = getattr(after, key)

        return diff

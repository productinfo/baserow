from typing import Any, Dict
from django.contrib.auth.models import AbstractUser
from rest_framework import serializers
from baserow.api.applications.serializers import ApplicationSerializer
from baserow.core.actions import DuplicateApplicationActionType

from baserow.core.exceptions import UserNotInGroup, GroupDoesNotExist
from baserow.core.handler import CoreHandler
from baserow.core.models import DuplicateApplicationJob
from baserow.core.jobs.registries import JobType
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP, ERROR_GROUP_DOES_NOT_EXIST

from baserow.core.action.registries import action_type_registry


class DuplicateApplicationJobType(JobType):
    type = "duplicate_application"
    model_class = DuplicateApplicationJob
    max_count = 1

    api_exceptions_map = {
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
    }

    request_serializer_field_names = ["application_id"]

    request_serializer_field_overrides = {
        "application_id": serializers.IntegerField(
            help_text="The application ID to duplicate.",
        ),
    }

    serializer_field_names = ["original_application", "duplicated_application"]
    serializer_field_overrides = {
        "original_application": ApplicationSerializer(read_only=True),
        "duplicated_application": ApplicationSerializer(read_only=True),
    }

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:

        application = CoreHandler().get_application(values.pop("application_id"))
        application.group.has_user(user, raise_error=True)

        return {
            "original_application": application,
        }

    def run(self, job, progress):

        user = job.restore_user_session()

        new_application_clone = action_type_registry.get_by_type(
            DuplicateApplicationActionType
        ).do(user, job.original_application.specific)

        progress.increment(100)

        # update the job with the new duplicated application
        job.duplicated_application = new_application_clone
        job.save(update_fields=("duplicated_application",))

        return new_application_clone

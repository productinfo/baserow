from rest_framework import serializers
from baserow.api.sessions import set_untrusted_client_session_id
from baserow.core.actions import DuplicateApplicationActionType

from baserow.core.exceptions import UserNotInGroup, GroupDoesNotExist
from baserow.core.handler import CoreHandler
from baserow.core.models import DuplicateApplicationJob
from baserow.core.signals import application_created
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

    serializer_field_names = ["application_id"]
    serializer_field_overrides = {
        "application_id": serializers.IntegerField(
            help_text="The application ID to duplicate.",
        ),
    }

    def prepare_values(self, values, user):

        application = CoreHandler().get_application(values.pop("application_id"))
        application.group.has_user(user, raise_error=True)

        return {"original_application": application}

    def run(self, job, progress):
        if job.user_session_id:
            set_untrusted_client_session_id(job.user, job.user_session_id)

        new_application_clone = action_type_registry.get_by_type(
            DuplicateApplicationActionType
        ).do(job.user, job.application)

        # update the job with the new duplicated application
        job.duplicated_application = new_application_clone
        job.save(update_fields=("duplicated_application",))

        application_created.send(self, application=new_application_clone, user=None)

        return new_application_clone

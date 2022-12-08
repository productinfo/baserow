from baserow.core.models import Group, GroupUser
from baserow.core.registries import SubjectType
from baserow_enterprise.api.role.serializers import SubjectGroupUserSerializer


class GroupUserSubjectType(SubjectType):
    type = "core.GroupUser"
    model_class = GroupUser

    def is_in_group(self, subject_id: int, group: Group) -> bool:
        return GroupUser.objects.filter(
            id=subject_id,
            group=group,
            user__profile__to_be_deleted=False,
            user__is_active=True,
        ).exists()

    def get_serializer(self, model_instance, **kwargs):
        return SubjectGroupUserSerializer(model_instance, **kwargs)

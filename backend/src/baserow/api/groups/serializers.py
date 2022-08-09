from rest_framework import serializers

from baserow.core.models import Group

from .users.serializers import GroupUserGroupSerializer, GroupUserSerializer

__all__ = [
    "GroupUserGroupSerializer",
    "GroupSerializer",
    "OrderGroupsSerializer",
    "GroupWithUsersSerializer",
]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = (
            "id",
            "name",
        )
        extra_kwargs = {"id": {"read_only": True}}


class GroupWithUsersSerializer(serializers.ModelSerializer):
    users = GroupUserSerializer(
        many=True, source="groupuser_set", required=False, read_only=True
    )

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "users",
        )
        extra_kwargs = {"id": {"read_only": True}}


class OrderGroupsSerializer(serializers.Serializer):
    groups = serializers.ListField(
        child=serializers.IntegerField(), help_text="Group ids in the desired order."
    )

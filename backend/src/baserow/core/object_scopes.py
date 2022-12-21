from django.db.models import Q

from baserow.core.models import Application, Group, GroupInvitation, GroupUser
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class CoreObjectScopeType(ObjectScopeType):
    model_class = type(None)
    type = "core"

    def get_filter_for_scope_type(self, scope_type, scopes):
        return None


class GroupObjectScopeType(ObjectScopeType):
    type = "group"
    model_class = Group

    def get_filter_for_scope_type(self, scope_type, scopes):
        return None


class ApplicationObjectScopeType(ObjectScopeType):
    type = "application"
    model_class = Application
    select_related = ["group"]

    def get_parent_scope(self):
        return object_scope_type_registry.get("group")

    def get_parent(self, context):
        return context.group

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(group__in=[s.id for s in scopes])

        return None


class GroupInvitationObjectScopeType(ObjectScopeType):
    type = "group_invitation"
    model_class = GroupInvitation
    select_related = ["group"]

    def get_parent_scope(self):
        return object_scope_type_registry.get("group")

    def get_parent(self, context):
        return context.group

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(group__in=[s.id for s in scopes])

        return None


class GroupUserObjectScopeType(ObjectScopeType):
    type = "group_user"
    model_class = GroupUser
    select_related = ["group"]

    def get_parent_scope(self):
        return object_scope_type_registry.get("group")

    def get_parent(self, context):
        return context.group

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(group__in=[s.id for s in scopes])

        return None

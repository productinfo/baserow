from django.db.models import Q

from baserow.contrib.database.models import Database
from baserow.core.object_scopes import GroupObjectScopeType
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class DatabaseObjectScopeType(ObjectScopeType):
    type = "database"
    model_class = Database
    select_related = ["group"]

    def get_parent_scope(self):
        return object_scope_type_registry.get("application")

    def get_parent(self, context):
        # Parent is the Application here even if it's at the "same" level
        # but it's a more generic type
        return context.application_ptr

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(group__in=[s.id for s in scopes])

        return None
